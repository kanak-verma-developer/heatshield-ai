"""LLM provider tests (Gemini / Claude) -- everything mocked, no network, no real keys."""
import json
import pytest
import requests

import backend.services.recommendations as rec
import backend.main as main_mod

DATA = {"risk_score": 62.0, "ndvi": 0.12, "built_up_density": 0.88, "road_density": 0.7,
        "wind_speed": 1.2, "water_proximity": 0.1, "surface_temp": 47.0}
DRIVERS = [{"feature": "built_up_density", "label": "built-up density", "zone_value": 0.88,
            "city_mean": 0.67, "risk_points_vs_city_avg": 7.2}]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "HEATSHIELD_LLM_PROVIDER", "GEMINI_MODEL"):
        monkeypatch.delenv(k, raising=False)


class FakeResp:
    def __init__(self, text, status=200):
        self.status_code, self._text = status, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code} for url with SECRET-KEY")

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": self._text}]}}]}


GOOD = json.dumps({"priority": "high", "reason": "Dense built-up area adds 7.2 points.",
                   "actions": ["Plant trees", "Cool roofs"], "expected_benefit": "Cooler streets",
                   "recommended_timeframe": "0-2 weeks"})


def test_no_key_means_rule_based():
    out = rec.get_recommendation("Budh Bazaar", DATA, drivers=DRIVERS)
    assert out["source"] == "RULE_BASED" and rec.active_provider() is None


def test_gemini_used_when_key_set_and_key_sent_in_header_only(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-KEY")
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, body=json, timeout=timeout)
        return FakeResp(GOOD)

    monkeypatch.setattr(rec.requests, "post", fake_post)
    out = rec.get_recommendation("Budh Bazaar", DATA, drivers=DRIVERS)
    assert out["source"] == "GEMINI_AI" and out["priority"] == "HIGH"
    assert out["actions"] == ["Plant trees", "Cool roofs"]
    assert "SECRET-KEY" not in seen["url"] and seen["headers"]["x-goog-api-key"] == "SECRET-KEY"
    assert "gemini-2.5-flash:generateContent" in seen["url"] and seen["timeout"] <= 15
    assert "Budh Bazaar" in seen["body"]["contents"][0]["parts"][0]["text"]


def test_gemini_model_is_configurable(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k"); monkeypatch.setenv("GEMINI_MODEL", "gemini-custom")
    urls = []
    monkeypatch.setattr(rec.requests, "post", lambda url, **k: urls.append(url) or FakeResp(GOOD))
    rec.get_recommendation("Z", DATA)
    assert "gemini-custom:generateContent" in urls[0]


def test_fenced_json_and_invalid_fields_are_normalised(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    messy = "```json\n" + json.dumps({"priority": "SUPER-URGENT", "actions": "not a list"}) + "\n```"
    monkeypatch.setattr(rec.requests, "post", lambda *a, **k: FakeResp(messy))
    out = rec.get_recommendation("Budh Bazaar", DATA, drivers=DRIVERS)
    base = rec._rule_based("Budh Bazaar", DATA, None, DRIVERS)
    assert out["source"] == "GEMINI_AI"
    assert out["priority"] == base["priority"]          # invalid -> rule-based value
    assert out["actions"] == base["actions"] and out["reason"] == base["reason"]


@pytest.mark.parametrize("bad", ["this is not json", "", "[1,2,3]"])
def test_garbage_reply_falls_back_to_rule_based(monkeypatch, bad):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(rec.requests, "post", lambda *a, **k: FakeResp(bad))
    out = rec.get_recommendation("Z", DATA)
    assert out["source"] == "RULE_BASED" and "Gemini" in out["note"]


def test_http_error_falls_back_and_never_leaks_key(monkeypatch, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-KEY")
    monkeypatch.setattr(rec.requests, "post", lambda *a, **k: FakeResp("", status=429))
    out = rec.get_recommendation("Z", DATA)
    assert out["source"] == "RULE_BASED"
    assert "SECRET-KEY" not in json.dumps(out) and "SECRET-KEY" not in capsys.readouterr().out


def test_timeout_falls_back(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    def boom(*a, **k): raise requests.Timeout("slow")
    monkeypatch.setattr(rec.requests, "post", boom)
    assert rec.get_recommendation("Z", DATA)["source"] == "RULE_BASED"


def test_provider_selection(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g"); monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert rec.active_provider() == "gemini"                       # default when both set
    monkeypatch.setenv("HEATSHIELD_LLM_PROVIDER", "claude")
    assert rec.active_provider() == ("claude" if rec._ANTHROPIC_AVAILABLE else None)
    monkeypatch.setenv("HEATSHIELD_LLM_PROVIDER", "none")
    assert rec.active_provider() is None


def test_data_sources_endpoint_reports_provider(monkeypatch):
    from fastapi.testclient import TestClient
    c = TestClient(main_mod.app)
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    names = {s["name"]: s["status"] for s in c.get("/api/data-sources").json()["sources"]}
    assert names["GenAI recommendations (Gemini / Claude)"] == "CONFIGURED (gemini)"


def test_dotenv_loader_does_not_override_real_env(monkeypatch, tmp_path):
    f = tmp_path / ".env"
    f.write_text('# comment\nGEMINI_API_KEY="from-file"\nHEATSHIELD_X=1\nEMPTY=\n')
    monkeypatch.delenv("HEATSHIELD_X", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "already-set")
    main_mod._load_dotenv(str(f))
    import os
    assert os.environ["GEMINI_API_KEY"] == "already-set" and os.environ["HEATSHIELD_X"] == "1"
    monkeypatch.delenv("HEATSHIELD_X")
