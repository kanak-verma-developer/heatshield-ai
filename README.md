# 🔥 HeatShield AI

### AI-Powered Urban Heat Intelligence & Mitigation Dashboard

HeatShield AI is a full-stack **Urban Heat Intelligence System** designed to monitor, analyze, and communicate heat-risk conditions for urban areas.

The platform combines **live weather data, machine learning, heat-risk scoring, zone-level analysis, hotspot detection, forecasting, explainable risk factors, historical tracking, and AI-assisted recommendations** into a single interactive dashboard.

The current prototype focuses on **Moradabad, Uttar Pradesh**.

---

## 🌐 Project Links

* 🌍 **Live Website:** https://heatshield-ai-75xc.onrender.com
* 💻 **GitHub Repository:** https://github.com/kanak-verma-developer/heatshield-ai

---

## ✨ Project Overview

Urban heat is influenced by multiple environmental and built-environment factors such as temperature, humidity, wind conditions, vegetation, built-up surfaces, and local land characteristics.

HeatShield AI converts these signals into an easy-to-understand **heat-risk intelligence dashboard**.

### The system provides:

* 🌡️ Live weather monitoring
* 🔥 Heat-risk scoring
* 🗺️ Zone-level heat analysis
* 📍 Hotspot identification
* 📊 Historical heat tracking
* 🔮 Short-term heat forecasting
* 🧠 Explainable risk factors
* 🤖 AI-powered recommendations
* ⚡ Real-time dashboard updates
* 🛡️ Rule-based fallback recommendations

---

## 🖥️ Project Preview

### Dashboard Overview

![HeatShield AI Dashboard](docs/screenshots/dashboard-overview.png)

### Zone Analysis

![HeatShield AI Zone Analysis](docs/screenshots/zone-analysis.png)

### AI Recommendations

![HeatShield AI AI Recommendations](docs/screenshots/ai-recommendations.png)

---

## 🚀 Key Features

### 🌡️ Live Weather Intelligence

HeatShield AI retrieves current weather information and uses it as an input for the heat-risk analysis.

The weather pipeline includes:

* Temperature
* Relative humidity
* Wind conditions
* Forecast information
* Current environmental conditions

---

### 🔥 AI-Based Heat Risk

The system processes environmental features through a machine-learning pipeline to generate heat-risk predictions.

The risk engine considers factors such as:

* Temperature
* Humidity
* Wind
* Vegetation
* Built-up environment
* Surface-related indicators
* Historical environmental patterns

The dashboard converts model output into an understandable risk level.

---

### 🗺️ Zone-Level Analysis

The city is divided into representative analysis zones.

Each zone can display:

* Heat-risk level
* Temperature conditions
* Vegetation characteristics
* Built-up characteristics
* Local heat indicators
* Risk contribution factors

This allows users to explore heat conditions beyond a single city-wide number.

---

### 📍 Hotspot Detection

HeatShield AI identifies zones showing comparatively higher heat-risk conditions.

The hotspot module helps highlight areas that may require additional attention during high-temperature conditions.

---

### 🔮 Heat Forecasting

The platform provides short-term forecasting information using available weather forecast data and the project's prediction pipeline.

Forecast views can help users understand how heat conditions may change over upcoming hours.

---

### 🧠 Explainable Risk Factors

Instead of displaying only a final score, the dashboard presents contributing environmental factors.

This makes the output easier to understand and provides context behind the generated risk level.

---

### 🤖 AI Recommendations

HeatShield AI can generate contextual recommendations based on the current heat conditions.

Recommendations can focus on areas such as:

* Public heat awareness
* Outdoor activity precautions
* Cooling strategies
* Water availability
* Vegetation and shade
* High-risk zones
* Community-level mitigation

The system also includes a **rule-based fallback**, allowing recommendations to continue when the AI service is unavailable.

---

### ⚡ Real-Time Updates

The backend supports real-time state updates so that the dashboard can reflect changing environmental information without requiring a complete application restart.

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │   Weather Sources    │
                    │   Live + Forecast    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Backend Services    │
                    │   FastAPI + Python    │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
      │ ML Pipeline │   │ Zone Engine │   │ Forecasting │
      └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Heat Intelligence    │
                    │ & Risk Analysis      │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │ Dashboard   │ │ Hotspots    │ │ AI Advice   │
        └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 🔄 Data → Intelligence → Action

```text
Environmental Data
        ↓
Data Processing
        ↓
Feature Engineering
        ↓
Machine Learning
        ↓
Heat Risk Analysis
        ↓
Zone & Hotspot Detection
        ↓
Forecasting
        ↓
AI / Rule-Based Recommendations
        ↓
Actionable Dashboard
```

---

## 🧠 Machine Learning

The project contains a complete machine-learning workflow:

* Dataset generation
* Feature preparation
* Model training
* Model serialization
* Prediction pipeline
* Residual analysis
* Model metadata
* Runtime inference

The trained model is included with the project so that a fresh deployment can run without requiring model training during startup.

### Important ML Note

The current training dataset is **synthetically generated** for prototype and engineering validation purposes.

Therefore, model metrics should **not be interpreted as real-world city-level prediction accuracy**.

The model demonstrates the complete ML pipeline and system integration rather than claiming validated operational accuracy for Moradabad.

---

## 📊 Data Transparency

HeatShield AI currently combines different levels of data maturity.

| Data Component          | Current Status       |
| ----------------------- | -------------------- |
| Live weather            | Connected            |
| Weather forecast        | Connected            |
| Historical runtime data | Working              |
| ML pipeline             | Working              |
| Zone information        | Prototype data       |
| Land-cover indicators   | Hand-set / estimated |
| Surface temperature     | Estimated            |
| Satellite data          | Not connected        |
| IoT sensor network      | Not connected        |

This distinction is intentionally documented so the project does not present prototype estimates as verified municipal or satellite measurements.

---

## 🛠️ Technology Stack

### Frontend

* HTML
* CSS
* JavaScript
* Leaflet
* Chart.js

### Backend

* Python
* FastAPI
* Uvicorn
* WebSocket

### Data & ML

* Pandas
* NumPy
* Scikit-learn
* Joblib

### AI

* Gemini API integration
* Rule-based recommendation fallback

### Storage

* SQLite

### Deployment

* Docker
* Render

---

## 📁 Project Structure

```text
heatshield-ai/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── models/
│   │   ├── heat_risk_model.joblib
│   │   ├── model_metadata.json
│   │   └── residuals_sample.json
│   └── services/
│       ├── db.py
│       ├── recommendations.py
│       ├── state.py
│       └── weather.py
│
├── data/
│   └── zones.py
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── MODEL_CARD.md
│   └── NEXT_STEPS.md
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── media/
│   └── vendor/
│
├── ml/
│   ├── forecasting.py
│   ├── generate_dataset.py
│   ├── hotspot_detection.py
│   └── train.py
│
├── tests/
│   ├── test_api.py
│   ├── test_model.py
│   ├── test_recommendations.py
│   ├── test_state.py
│   └── test_status.py
│
├── Dockerfile
├── README.md
├── .env.example
└── .gitignore
```

---

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/kanak-verma-developer/heatshield-ai.git
cd heatshield-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 5. Configure environment variables

Create a `.env` file based on `.env.example`.

```env
GEMINI_API_KEY=YOUR_API_KEY
HEATSHIELD_LLM_PROVIDER=gemini
```

Keep API keys private and never commit `.env` to GitHub.

### 6. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

The application will be available on the local server.

---

## 🧪 Testing

The project includes automated tests covering important backend components.

Test categories include:

* API endpoints
* Model behaviour
* Recommendation logic
* Application state
* Application status

Run:

```bash
pytest
```

---

## 🐳 Docker

The project includes a Docker configuration for containerized deployment.

Build:

```bash
docker build -t heatshield-ai .
```

Run:

```bash
docker run -p 8000:8000 heatshield-ai
```

---

## 🔐 Security

The project follows basic application security practices:

* API keys are stored through environment variables.
* `.env` files are excluded from Git.
* Secrets are not included in source code.
* Gemini credentials are handled through backend configuration.
* Runtime-generated database files are excluded from version control.

---

## ⚠️ Current Limitations

HeatShield AI is currently a **prototype / engineering project** and has several limitations.

### Data Limitations

* Current zone boundaries are representative rather than official municipal boundaries.
* Some land-cover values are estimated.
* Surface temperature is currently estimated rather than retrieved from live satellite-derived LST.
* Satellite integration is not currently active.
* IoT sensor hardware is not currently connected.

### ML Limitations

* Training data is synthetic.
* Model performance has not been validated against a large real-world Moradabad heat dataset.
* Model metrics therefore should not be treated as operational accuracy.

### Deployment Limitations

The free deployment environment may temporarily suspend the application after periods of inactivity, which can result in a slower first request after inactivity.

---

## 🗺️ Future Roadmap

### Phase 1 — Current Prototype

* Live weather
* Heat-risk prediction
* Zone analysis
* Hotspot detection
* Forecasting
* AI recommendations
* Historical tracking
* Interactive dashboard

### Phase 2 — Data Expansion

* Satellite-derived land-surface temperature
* NDVI integration
* Improved land-cover classification
* Higher-resolution spatial analysis
* Larger real-world datasets

### Phase 3 — IoT Integration

* ESP32 sensor nodes
* Temperature monitoring
* Humidity monitoring
* Air-quality sensing
* Noise monitoring
* Local environmental telemetry

### Phase 4 — Advanced Intelligence

* Improved real-world ML models
* More accurate spatial predictions
* Automated anomaly detection
* Advanced forecasting
* Community-level heat alerts

---

## 💡 Project Highlights

HeatShield AI demonstrates the integration of:

* Full-stack web development
* Machine learning
* Environmental data processing
* Real-time APIs
* Geospatial visualization
* Data analysis
* AI-assisted recommendations
* Backend API development
* Docker deployment
* Automated testing
* Responsible data documentation

---

## 🎯 What This Project Demonstrates

### Software Engineering

* REST API development
* Backend architecture
* Frontend integration
* State management
* Database integration
* Real-time communication
* Containerized deployment

### Artificial Intelligence

* Machine-learning pipeline
* Feature engineering
* Prediction workflows
* Explainable risk factors
* AI-generated recommendations
* Fallback intelligence

### Data Science

* Environmental data processing
* Feature analysis
* Forecasting
* Historical tracking
* Hotspot identification
* Data transparency

### Product Thinking

The system is designed around a simple workflow:

**Observe → Analyze → Explain → Recommend → Act**

---

## 🌱 Project Vision

HeatShield AI aims to demonstrate how environmental data, machine learning, and accessible web technology can be combined to create practical tools for understanding urban heat.

The long-term vision is to move from a prototype dashboard toward a richer urban climate intelligence platform using **real satellite data, sensor networks, validated datasets, and improved predictive models**.

---

## 👩‍💻 Built By

**Kanak Verma**

B.Tech — Computer Science & Engineering (Data Science)

Focused on **Full-Stack Development, AI/ML, and practical technology solutions**.

---

## 📌 Project Status

**Current Status: Prototype → Deployed**

The application is deployed and functional, with live weather integration, ML-based risk analysis, zone intelligence, forecasting, AI recommendations, and a documented roadmap for future real-world data integration.

---

## 🔗 Repository

**GitHub:** https://github.com/kanak-verma-developer/heatshield-ai
