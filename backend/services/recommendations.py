"""
HeatShield AI - Recommendation Engine

Modes:
  - RULE_BASED
  - GEMINI_AI
  - CLAUDE_AI

Gemini model fallback:
  1. gemini-3.8-flash
  2. gemini-3.7-flash
  3. gemini-3.6-flash
  4. gemini-3.5-flash
  5. gemini-2.5-flash

If all LLM attempts fail, the system ALWAYS falls back
to the deterministic RULE_BASED engine.

The frontend never receives or sees API keys.
"""

import json
import os
import time

import requests


# ============================================================
# GEMINI MODELS
# ============================================================

GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"

# Automatic fallback order.
# If the first model fails, the next one is tried automatically.
GEMINI_FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]


# ============================================================
# OPTIONAL CLAUDE SUPPORT
# ============================================================

try:
    import anthropic

    _ANTHROPIC_AVAILABLE = True

except ImportError:
    _ANTHROPIC_AVAILABLE = False


# ============================================================
# FEATURE LABELS
# ============================================================

_FEATURE_LABELS = {
    "surface_temp": "surface temperature",
    "built_up_density": "built-up/construction density",
    "ndvi": "vegetation cover (NDVI)",
    "air_temp": "air temperature",
    "road_density": "road/paved-surface density",
    "water_proximity": "distance from water bodies",
    "humidity": "humidity",
    "wind_speed": "wind speed",
}


# ============================================================
# RULE-BASED ENGINE
# ============================================================

def _rule_based(
    zone_name: str,
    data: dict,
    feature_importance: dict = None,
    drivers: list = None,
) -> dict:

    risk = data["risk_score"]
    ndvi = data["ndvi"]
    built_up = data["built_up_density"]

    road_density = data.get("road_density", 0.5)
    wind_speed = data.get("wind_speed", 2.0)
    water_proximity = data.get("water_proximity", 0.5)
    surface_temp = data.get("surface_temp", 0)

    actions = []

    # --------------------------------------------------------
    # Green cover
    # --------------------------------------------------------

    if built_up > 0.7 and ndvi < 0.25:
        actions.append(
            "Increase green cover / urban tree plantation in dense built-up corridors"
        )

    # --------------------------------------------------------
    # Surface temperature
    # --------------------------------------------------------

    if surface_temp > 45:
        actions.append(
            "Deploy cool-roof / reflective-surface program for high-LST buildings"
        )

    # --------------------------------------------------------
    # High heat risk
    # --------------------------------------------------------

    if risk > 70:
        actions.append(
            "Set up temporary shaded cooling zones for high-footfall areas"
        )

    # --------------------------------------------------------
    # Water proximity
    # --------------------------------------------------------

    if water_proximity < 0.3:
        actions.append(
            "Explore small-scale water body restoration or misting stations"
        )

    # --------------------------------------------------------
    # Roads
    # --------------------------------------------------------

    if road_density > 0.6:
        actions.append(
            "Use permeable/light-colored pavement and tree-lined boulevards "
            "on major roads to cut asphalt heat retention"
        )

    # --------------------------------------------------------
    # Wind / ventilation
    # --------------------------------------------------------

    if wind_speed < 1.5 and built_up > 0.6:
        actions.append(
            "Preserve open-air ventilation corridors between buildings; "
            "avoid further wall-to-wall construction that traps hot air"
        )

    # --------------------------------------------------------
    # Default action
    # --------------------------------------------------------

    if not actions:
        actions.append(
            "Continue routine monitoring; no urgent mitigation action required"
        )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    if risk > 85:
        priority = "CRITICAL"

    elif risk > 70:
        priority = "HIGH"

    elif risk > 50:
        priority = "MEDIUM"

    else:
        priority = "LOW"

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    if drivers:

        top = [
            d
            for d in drivers
            if abs(d["risk_points_vs_city_avg"]) >= 0.5
        ][:2]

        if top:

            parts = [
                (
                    f"{d['label']} ({d['zone_value']} vs city mean "
                    f"{d['city_mean']}) "
                    f"{'adds' if d['risk_points_vs_city_avg'] > 0 else 'removes'} "
                    f"about {abs(d['risk_points_vs_city_avg']):.1f} risk points"
                )
                for d in top
            ]

            reason = (
                f"{zone_name} shows a heat risk of {risk}/100. "
                f"Compared with an average Moradabad zone, the model attributes: "
                + "; ".join(parts)
                + "."
            )

        else:

            reason = (
                f"{zone_name} shows a heat risk of {risk}/100, close to "
                f"what the model predicts for an average Moradabad zone."
            )

    elif feature_importance:

        ranked = sorted(
            feature_importance.items(),
            key=lambda kv: -kv[1],
        )

        top_feat, top_pct = ranked[0]

        reason = (
            f"{zone_name} shows a heat risk of {risk}/100. "
            f"Across all zones the saved model weights "
            f"{_FEATURE_LABELS.get(top_feat, top_feat)} most heavily "
            f"(~{top_pct}% estimated importance)."
        )

    else:

        reason = (
            f"{zone_name} shows a heat risk of {risk}/100, driven mainly by "
            f"{'high built-up density' if built_up > 0.6 else 'moderate built-up density'} "
            f"and "
            f"{'low vegetation cover' if ndvi < 0.25 else 'moderate vegetation cover'}."
        )

    return {
        "source": "RULE_BASED",
        "zone": zone_name,
        "priority": priority,
        "reason": reason,
        "actions": actions[:4],
        "expected_benefit": (
            "Localized reduction in surface temperature and improved thermal comfort"
            if risk > 60
            else "Maintains current conditions"
        ),
        "recommended_timeframe": (
            "Immediate (0-2 weeks)"
            if priority in ("CRITICAL", "HIGH")
            else "Next planning cycle (1-3 months)"
        ),
    }


# ============================================================
# GEMINI PROMPT
# ============================================================

def _build_prompt(
    zone_name,
    data,
    feature_importance,
    drivers,
):

    fi_note = ""

    if feature_importance:
        fi_note += (
            f"\nModel feature importance (global, %): "
            f"{feature_importance}"
        )

    if drivers:
        fi_note += (
            f"\nZone-specific model attribution vs city-average "
            f"zone (risk points): {drivers}"
        )

    return (
        "You are an urban climate-mitigation advisor for HeatShield AI. "
        "Using ONLY the structured data below, generate a concise recommendation. "
        "Do NOT invent measurements, locations, weather values, satellite values, "
        "or statistics that are not present in the supplied data. "
        "If a value is estimated or simulated, do not present it as a direct measurement. "
        "\n\n"
        "Return ONLY a valid JSON object with exactly these fields:\n"
        "{\n"
        '  "priority": "LOW | MEDIUM | HIGH | CRITICAL",\n'
        '  "reason": "1-2 concise sentences",\n'
        '  "actions": ["short action 1", "short action 2", "short action 3"],\n'
        '  "expected_benefit": "one concise sentence",\n'
        '  "recommended_timeframe": "short timeframe"\n'
        "}\n\n"
        f"Zone: {zone_name}\n"
        f"Data: {data}"
        f"{fi_note}"
    )


# ============================================================
# JSON PARSER
# ============================================================

def _parse_json(text: str) -> dict:

    cleaned = text.strip()

    # Remove Markdown fences if model accidentally returns them.
    if cleaned.startswith("```"):

        cleaned = cleaned.strip("`")

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]

    cleaned = cleaned.strip()

    # Try normal JSON first.
    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:

        # Sometimes models return extra text around JSON.
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1 and end > start:

            extracted = cleaned[start:end + 1]

            return json.loads(extracted)

        raise


# ============================================================
# OUTPUT NORMALIZER
# ============================================================

def _normalize(
    parsed: dict,
    fallback: dict,
    source: str,
    zone_name: str,
) -> dict:

    """
    Never trust LLM output blindly.

    Only expected fields are returned.
    Invalid/missing values fall back to the deterministic engine.
    """

    out = {
        "source": source,
        "zone": zone_name,
    }

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    pr = str(
        parsed.get("priority", "")
    ).upper().strip()

    if pr in (
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ):
        out["priority"] = pr
    else:
        out["priority"] = fallback["priority"]

    # --------------------------------------------------------
    # Reason
    # --------------------------------------------------------

    reason = parsed.get("reason")

    if reason:
        out["reason"] = str(reason)[:600]

    else:
        out["reason"] = fallback["reason"]

    # --------------------------------------------------------
    # Actions
    # --------------------------------------------------------

    acts = parsed.get("actions")

    if isinstance(acts, list):

        acts = [
            str(a)[:300]
            for a in acts
            if a
        ]

    else:
        acts = []

    out["actions"] = acts[:4] or fallback["actions"]

    # --------------------------------------------------------
    # Expected benefit
    # --------------------------------------------------------

    benefit = parsed.get("expected_benefit")

    if benefit:
        out["expected_benefit"] = str(benefit)[:300]

    else:
        out["expected_benefit"] = fallback["expected_benefit"]

    # --------------------------------------------------------
    # Timeframe
    # --------------------------------------------------------

    timeframe = parsed.get("recommended_timeframe")

    if timeframe:
        out["recommended_timeframe"] = str(timeframe)[:100]

    else:
        out["recommended_timeframe"] = fallback[
            "recommended_timeframe"
        ]

    return out


# ============================================================
# GEMINI REST CALL
# ============================================================

def _call_gemini(
    api_key: str,
    prompt: str,
) -> tuple[str, str]:

    """
    Try Gemini models one by one.

    Order:

        Gemini 3.8 Flash
             ↓ failure
        Gemini 3.7 Flash
             ↓ failure
        Gemini 3.6 Flash
             ↓ failure
        Gemini 3.5 Flash
             ↓ failure
        Gemini 2.5 Flash
             ↓ failure
        RULE_BASED fallback

    Returns:

        (response_text, model_used)
    """

    configured_model = os.environ.get(
        "GEMINI_MODEL",
        ""
    ).strip()

    # If user explicitly configured a model,
    # try that one first.
    if configured_model:

        models = [
            configured_model
        ] + [
            model
            for model in GEMINI_FALLBACK_MODELS
            if model != configured_model
        ]

    else:

        models = GEMINI_FALLBACK_MODELS

    errors = []

    for model in models:

        try:

            print(
                f"[recommendations] Trying Gemini model: {model}"
            )

            url = (
                "https://generativelanguage.googleapis.com/"
                f"v1beta/models/{model}:generateContent"
            )

            response = requests.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "maxOutputTokens": 1024,
                    },
                },
                timeout=15,
            )

            response.raise_for_status()

            body = response.json()

            candidates = body.get(
                "candidates",
                []
            )

            if not candidates:
                raise RuntimeError(
                    "Gemini returned no candidates"
                )

            content = candidates[0].get(
                "content",
                {}
            )

            parts = content.get(
                "parts",
                []
            )

            text = "".join(
                part.get("text", "")
                for part in parts
                if isinstance(part, dict)
            )

            if not text.strip():
                raise RuntimeError(
                    "Gemini returned an empty response"
                )

            print(
                f"[recommendations] Gemini success: {model}"
            )

            return text, model

        except Exception as exc:

            error_name = type(exc).__name__

            errors.append(
                f"{model}: {error_name}"
            )

            print(
                f"[recommendations] Gemini {model} failed: "
                f"{error_name}"
            )

            # Automatically continue to next model.
            continue

    # Every Gemini model failed.
    raise RuntimeError(
        "All Gemini models failed: "
        + ", ".join(errors)
    )


# ============================================================
# CLAUDE REST/SDK CALL
# ============================================================

def _call_claude(
    api_key: str,
    prompt: str,
) -> str:

    if not _ANTHROPIC_AVAILABLE:

        raise RuntimeError(
            "Anthropic package is not installed"
        )

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=15.0,
        max_retries=1,
    )

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return "".join(
        block.text
        for block in msg.content
        if getattr(block, "type", "") == "text"
    )


# ============================================================
# LLM STATE
# ============================================================

_llm_state = {
    "provider": None,
    "model": None,
    "last_ok": None,
    "last_error": None,
    "ts": None,
}


def llm_status():
    """
    Returns the outcome of the most recent LLM attempt.
    Used by /api/status.
    """

    return dict(_llm_state)


# ============================================================
# ACTIVE PROVIDER
# ============================================================

def active_provider():
    """
    Returns:

        "gemini"
        "claude"
        None

    Priority is controlled by:

        HEATSHIELD_LLM_PROVIDER

    If both keys exist and provider is not specified,
    Gemini is preferred.
    """

    gemini_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    claude_key = os.environ.get(
        "ANTHROPIC_API_KEY"
    )

    choice = os.environ.get(
        "HEATSHIELD_LLM_PROVIDER",
        "",
    ).lower().strip()

    # Explicitly disabled.
    if choice == "none":
        return None

    # Explicit Gemini.
    if choice == "gemini":

        if gemini_key:
            return "gemini"

        return None

    # Explicit Claude.
    if choice == "claude":

        if claude_key and _ANTHROPIC_AVAILABLE:
            return "claude"

        return None

    # Default:
    # Gemini first.
    if gemini_key:
        return "gemini"

    # Claude second.
    if claude_key and _ANTHROPIC_AVAILABLE:
        return "claude"

    return None


# ============================================================
# MAIN RECOMMENDATION FUNCTION
# ============================================================

def get_recommendation(
    zone_name: str,
    data: dict,
    feature_importance: dict = None,
    drivers: list = None,
) -> dict:

    """
    Main recommendation entry point.

    Flow:

        1. Build deterministic rule-based recommendation.
        2. Check configured provider.
        3. Try Gemini model cascade if Gemini selected.
        4. Validate and normalize AI response.
        5. If AI fails, return RULE_BASED fallback.
    """

    # --------------------------------------------------------
    # Always prepare safe fallback first.
    # --------------------------------------------------------

    fallback = _rule_based(
        zone_name,
        data,
        feature_importance,
        drivers,
    )

    provider = active_provider()

    # --------------------------------------------------------
    # No LLM configured.
    # --------------------------------------------------------

    if provider is None:

        _llm_state.update(
            provider=None,
            model=None,
            last_ok=None,
            last_error=None,
            ts=time.time(),
        )

        return fallback

    try:

        prompt = _build_prompt(
            zone_name,
            data,
            feature_importance,
            drivers,
        )

        # ====================================================
        # GEMINI
        # ====================================================

        if provider == "gemini":

            text, model_used = _call_gemini(
                os.environ["GEMINI_API_KEY"],
                prompt,
            )

            source = "GEMINI_AI"

            result = _normalize(
                _parse_json(text),
                fallback,
                source,
                zone_name,
            )

            _llm_state.update(
                provider="gemini",
                model=model_used,
                last_ok=True,
                last_error=None,
                ts=time.time(),
            )

            # Add model information internally/usefully.
            # This doesn't expose the API key.
            result["model"] = model_used

            return result

        # ====================================================
        # CLAUDE
        # ====================================================

        if provider == "claude":

            text = _call_claude(
                os.environ["ANTHROPIC_API_KEY"],
                prompt,
            )

            source = "CLAUDE_AI"

            result = _normalize(
                _parse_json(text),
                fallback,
                source,
                zone_name,
            )

            _llm_state.update(
                provider="claude",
                model="claude-sonnet-4-6",
                last_ok=True,
                last_error=None,
                ts=time.time(),
            )

            result["model"] = "claude-sonnet-4-6"

            return result

        # Unknown provider.
        raise RuntimeError(
            f"Unsupported provider: {provider}"
        )

    except Exception as exc:

        # ----------------------------------------------------
        # NEVER expose API key or sensitive request details.
        # ----------------------------------------------------

        error_name = type(exc).__name__

        print(
            f"[recommendations] {provider} call failed: "
            f"{error_name}"
        )

        _llm_state.update(
            provider=provider,
            model=None,
            last_ok=False,
            last_error=error_name,
            ts=time.time(),
        )

        # ----------------------------------------------------
        # Safe fallback.
        # ----------------------------------------------------

        fallback["note"] = (
            f"{provider.capitalize()} call failed or unavailable; "
            "showing rule-based fallback."
        )

        return fallback