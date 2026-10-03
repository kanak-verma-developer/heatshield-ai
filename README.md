# 🔥 HeatShield AI

### AI-Powered Urban Heat Intelligence & Mitigation Dashboard

> **Monitoring urban heat risk across Moradabad, Uttar Pradesh — combining live weather, machine learning, hotspot detection, forecasting, and AI-generated recommendations in one dashboard.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikit-learn\&logoColor=white)](https://scikit-learn.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?logo=javascript\&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Leaflet](https://img.shields.io/badge/Leaflet-Maps-199900?logo=leaflet\&logoColor=white)](https://leafletjs.com/)
[![Gemini](https://img.shields.io/badge/Gemini-AI%20Recommendations-4285F4?logo=google\&logoColor=white)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker\&logoColor=white)](https://www.docker.com/)

---

## 🌍 Overview

**HeatShield AI** is a full-stack urban heat intelligence prototype designed to help visualize and understand heat-risk conditions across different zones of **Moradabad, Uttar Pradesh**.

The system combines:

* 🌤️ Live weather data
* 🤖 Machine-learning based heat-risk scoring
* 🗺️ Zone-level heat visualization
* 🔥 Hotspot detection
* 📈 Short-term forecasting
* 💡 Explainable risk factors
* 🧠 Gemini-powered recommendations
* 📊 Historical trend tracking
* ⚡ REST APIs + WebSocket live updates

The goal is to turn environmental data into **simple, actionable information** for understanding where heat risk may be higher and what mitigation measures could be considered.

---

# 🎥 Demo Preview

### Dashboard

> Add your latest dashboard screenshot here.

```text
docs/screenshots/dashboard-overview.png
```

![HeatShield AI Dashboard](docs/screenshots/dashboard-overview.png)

### Heat Risk & Zone Analysis

![HeatShield AI Zone Analysis](docs/screenshots/zone-analysis.png)

### AI Recommendations

![HeatShield AI Recommendations](docs/screenshots/ai-recommendations.png)

> **Tip:** The screenshots above should be captured from the running dashboard at `http://localhost:8000/`.

---

# ✨ Key Features

## 🌤️ Live Weather Monitoring

HeatShield AI connects to **Open-Meteo** to retrieve current weather information such as:

* Temperature
* Relative humidity
* Wind speed
* Hourly forecast

Live weather is clearly marked as **LIVE** in the dashboard.

---

## 🔥 Zone-Level Heat Risk

The city is divided into multiple monitored zones.

Each zone receives a heat-risk score based on environmental features and the trained ML model.

The dashboard provides:

* Risk score
* Risk category
* Zone comparison
* Hotspot identification
* Factor-level explanation

---

## 🗺️ Interactive Heat Map

The dashboard provides a map-based view of the monitored zones.

Users can quickly identify areas with comparatively higher or lower estimated heat risk.

> Zone coordinates and land-cover features are currently prototype-level inputs rather than official municipal boundaries.

---

## 🤖 AI-Powered Recommendations

When Gemini is configured, HeatShield AI generates contextual recommendations for individual zones.

Examples of intervention categories include:

* 🌳 Increasing vegetation
* 🏠 Cool-roof strategies
* 🌤️ Increasing shade
* 🚶 Improving shaded pedestrian areas
* 💧 Heat-response measures

The system automatically falls back to rule-based recommendations if the AI service is unavailable.

---

## 📈 Heat Forecasting

The system generates a short-term **1–48 hour forecast** using the available weather forecast and the heat-risk model.

The dashboard can show:

* Forecast trend
* Expected risk changes
* Uncertainty information
* Current vs predicted conditions

---

## 🔎 Explainable Heat Risk

Instead of only showing a number, the system attempts to explain **why a zone receives its risk score**.

Zone-level factors can include:

* Built-up density
* Vegetation estimate
* Road density
* Water proximity
* Environmental conditions

This makes the output easier to interpret than a black-box risk score.

---

## 🚨 Hotspot Detection

HeatShield AI identifies potentially important zones using a combination of:

* Risk thresholds
* Statistical comparison
* Zone-level feature differences

Hotspots are highlighted in the dashboard for quick inspection.

---

## ⚡ Real-Time Dashboard Updates

The backend exposes a WebSocket endpoint:

```text
/ws/live
```

The dashboard receives updated system information without requiring a full page reload.

---

## 🧪 Built-In Testing

The project includes automated tests covering:

* API behaviour
* Model functionality
* Recommendation logic
* Application state
* System status

Current repository includes **68 tests**.

---

# 🧠 System Architecture

```text
                         ┌──────────────────────┐
                         │     Open-Meteo       │
                         │   Live Weather API   │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                      │
│                                                         │
│  Weather Service → State Management → ML Pipeline      │
│                         │                               │
│                         ├── Hotspot Detection           │
│                         ├── Forecasting                 │
│                         ├── Explainability              │
│                         └── AI Recommendations          │
└───────────────────────┬─────────────────────────────────┘
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
       REST API              WebSocket
     /api/...                 /ws/live
             │                     │
             └──────────┬──────────┘
                        ▼
              ┌───────────────────┐
              │   Web Dashboard   │
              │ HTML/CSS/JS       │
              │ Leaflet + Chart.js│
              └───────────────────┘
```

### Data → Intelligence → Action

```text
Weather Data
     │
     ▼
Zone Features
     │
     ▼
Machine Learning Model
     │
     ├──────────────► Heat Risk Score
     │
     ├──────────────► Hotspot Detection
     │
     ├──────────────► Forecast
     │
     └──────────────► Explanation
                         │
                         ▼
                  Gemini AI / Rules
                         │
                         ▼
                Actionable Recommendations
```

---

# 🛠️ Tech Stack

| Layer                | Technologies                |
| -------------------- | --------------------------- |
| **Frontend**         | HTML5, CSS3, JavaScript     |
| **Visualization**    | Chart.js                    |
| **Mapping**          | Leaflet                     |
| **Backend**          | Python, FastAPI             |
| **Real-time**        | WebSocket                   |
| **Machine Learning** | scikit-learn, Pandas, NumPy |
| **Weather Data**     | Open-Meteo                  |
| **Generative AI**    | Google Gemini API           |
| **Data Storage**     | SQLite runtime history      |
| **Model Storage**    | Joblib                      |
| **Testing**          | Pytest                      |
| **Deployment**       | Docker                      |
| **Version Control**  | Git + GitHub                |

---

# 📁 Project Structure

```text
heatshield-ai/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   │
│   ├── models/
│   │   ├── heat_risk_model.joblib
│   │   ├── model_metadata.json
│   │   └── residuals_sample.json
│   │
│   └── services/
│       ├── db.py
│       ├── recommendations.py
│       ├── state.py
│       └── weather.py
│
├── data/
│   └── zones.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── media/
│   └── vendor/
│
├── ml/
│   ├── generate_dataset.py
│   ├── train.py
│   ├── forecasting.py
│   └── hotspot_detection.py
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── MODEL_CARD.md
│   ├── NEXT_STEPS.md
│   └── CHANGELOG.md
│
├── tests/
│   ├── test_api.py
│   ├── test_model.py
│   ├── test_recommendations.py
│   ├── test_state.py
│   └── test_status.py
│
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/kanak-verma-developer/heatshield-ai.git
cd heatshield-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Optional — enable Gemini recommendations

Create `.env` in the project root:

```env
GEMINI_API_KEY=your_api_key_here
HEATSHIELD_LLM_PROVIDER=gemini
```

**Never commit `.env` to GitHub.**

### 5. Start the application

```bash
uvicorn backend.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/
```

API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/api/health
```

---

# 🐳 Docker

Build:

```bash
docker build -t heatshield-ai .
```

Run:

```bash
docker run -p 8000:8000 heatshield-ai
```

Then open:

```text
http://localhost:8000/
```

---

# 🧪 Testing

Install development dependencies:

```bash
pip install -r backend/requirements-dev.txt
```

Run tests:

```bash
pytest tests/ -v
```

The project currently contains **68 automated tests**.

---

# 📊 Data Transparency

HeatShield AI intentionally distinguishes between real data, estimates, simulations, and unavailable sources.

| Data / Component          | Current Status                         |
| ------------------------- | -------------------------------------- |
| Current weather           | 🟢 **LIVE** — Open-Meteo               |
| Hourly forecast           | 🟢 **LIVE** — Open-Meteo               |
| ML pipeline               | 🟢 **WORKING**                         |
| Historical dashboard data | 🟢 **WORKING**                         |
| Gemini recommendations    | 🟢 **LIVE when API key is configured** |
| Zone land-cover values    | 🟡 **ESTIMATE**                        |
| Surface temperature       | 🟡 **ESTIMATE**                        |
| Zone boundaries           | 🟡 **APPROXIMATE**                     |
| ML training dataset       | 🟠 **SYNTHETIC**                       |
| Satellite data            | ⚪ **NOT CONNECTED**                    |
| IoT sensors               | ⚪ **NOT CONNECTED**                    |

### Important ML limitation

The current model is trained on **synthetic data**.

Therefore, reported model metrics such as R² describe performance on that synthetic dataset and **should not be interpreted as validated real-world prediction accuracy**.

Real-world validation would require reliable historical environmental and ground-truth heat-risk data.

---

# 🔐 Security

* API keys are loaded through environment variables.
* `.env` is excluded through `.gitignore`.
* No Gemini API key is stored in frontend code.
* `.env.example` contains placeholders only.

---

# 🗺️ Future Roadmap

### Data

* [ ] Integrate Sentinel-2 / Landsat derived environmental features
* [ ] Add reliable land-surface temperature data
* [ ] Replace hand-set zone priors with measured datasets
* [ ] Add official GIS boundaries where available

### Intelligence

* [ ] Validate model using real-world historical data
* [ ] Improve calibration across seasons
* [ ] Add uncertainty-aware risk estimation
* [ ] Expand forecasting capabilities

### Platform

* [ ] Add user authentication
* [ ] Add notification / alert system
* [ ] Add city-level scalability
* [ ] Deploy production backend
* [ ] Add monitoring and observability

---

# 📚 Documentation

* [`API.md`](docs/API.md) — API endpoints
* [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system architecture
* [`DATA_SOURCES.md`](docs/DATA_SOURCES.md) — data sources and limitations
* [`MODEL_CARD.md`](docs/MODEL_CARD.md) — model details and limitations
* [`NEXT_STEPS.md`](docs/NEXT_STEPS.md) — development roadmap
* [`CHANGELOG.md`](docs/CHANGELOG.md) — project changes

---

# 🌱 Why HeatShield AI?

HeatShield AI explores how **machine learning + environmental data + real-time dashboards + generative AI** can be combined to make urban heat information easier to understand and act upon.

The project is designed as a transparent prototype: where real data is available, it is labelled as live; where assumptions or synthetic data are used, they are explicitly identified.

---

## 👩‍💻 Built By

**Kanak Verma**

B.Tech — Computer Science & Engineering (Data Science)

Moradabad, Uttar Pradesh, India

**Focus:** Full-Stack Development • AI/ML • Data-Driven Applications

---

⭐ If you find the project interesting, consider starring the repository.

[GitHub Repository](https://github.com/kanak-verma-developer/heatshield-ai)
