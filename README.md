# 🔥 HeatShield AI

### AI-Powered Urban Heat Intelligence & Mitigation Dashboard

> **A full-stack environmental intelligence platform designed to visualize urban heat risk across Moradabad, Uttar Pradesh using live weather data, machine learning, forecasting, hotspot detection, and AI-powered recommendations.**

---

## 🌍 Overview

**HeatShield AI** is a full-stack AI/ML project focused on understanding and visualizing **urban heat risk at the zone level**.

The platform combines environmental data, machine learning, interactive visualization, forecasting, and generative AI to transform complex heat-related information into an easy-to-understand dashboard.

The system is designed around a simple flow:

```text
Environmental Data
       ↓
Zone-Level Analysis
       ↓
Machine Learning
       ↓
Heat Risk Estimation
       ↓
Hotspot Detection
       ↓
Forecasting
       ↓
AI Recommendations
```

The project currently focuses on **Moradabad, Uttar Pradesh** as the prototype study area.

> ⚠️ **Transparency:** Some environmental features and training data are currently synthetic or estimated. They are clearly labelled in the application and should not be interpreted as official measurements.

---

# 🎥 Project Preview

## 📊 Main Dashboard

The main dashboard provides a centralized view of the current urban heat situation.

It includes:

* Current temperature
* Average heat-risk score
* Number of detected danger zones
* Hottest estimated surface temperature
* Greenery indicator
* Zone-level risk
* Interactive map
* Current system status

![HeatShield AI Dashboard](docs/screenshots/dashboard-overview.png)

---

## 🗺️ Zone & Heat Analysis

The zone analysis interface allows users to inspect individual areas and understand their estimated heat-risk conditions.

It can display:

* Zone risk score
* Risk category
* Environmental factors
* Hotspot status
* Zone comparison
* Heat-risk explanation

![HeatShield AI Zone Analysis](docs/screenshots/zone-analysis.png)

---

## 🤖 AI Recommendations

HeatShield AI can generate zone-specific recommendations using Gemini when the API is configured.

Recommendations are designed around possible urban heat mitigation actions such as:

* Increasing vegetation
* Improving shade
* Cool-roof strategies
* Heat-response measures
* Improving pedestrian comfort
* Reducing heat exposure

![AI Recommendations](docs/screenshots/ai-recommendations.png)

> If Gemini is unavailable, the application automatically falls back to its rule-based recommendation engine.

---

# ✨ Key Features

## 🌤️ 1. Live Weather Monitoring

The application retrieves current weather information and hourly forecast data.

Current weather inputs include:

* 🌡️ Temperature
* 💧 Relative humidity
* 💨 Wind speed
* 📈 Hourly forecast

The dashboard distinguishes live weather information from estimated or simulated environmental values.

---

## 🔥 2. Zone-Level Heat Risk

Moradabad is represented through multiple monitored zones.

Each zone receives an estimated heat-risk score based on environmental features and the machine-learning pipeline.

The dashboard makes it possible to compare zones and quickly identify areas with comparatively higher estimated risk.

### Example monitored zones

```text
Civil Lines
Katghar
Majhola
Pakwara
Asalatpura
Galshaheed
Budh Bazaar
Moradabad Central
Rampur Road
Delhi Road
New Moradabad
```

---

# 🗺️ 3. Interactive Heat Map

The dashboard includes an interactive map for visualizing zone-level heat conditions.

The map helps users quickly understand:

```text
LOW RISK
   ↓
MODERATE RISK
   ↓
HIGH RISK
   ↓
HOTSPOT
```

Each monitored location can be inspected individually.

> Current map locations are prototype-level coordinates and do not represent official municipal ward boundaries.

---

# 🤖 4. AI-Powered Recommendations

HeatShield AI integrates **Gemini** as an optional recommendation engine.

For a selected zone, the system can provide contextual recommendations based on available environmental information.

### Recommendation flow

```text
Selected Zone
      ↓
Environmental Features
      ↓
Heat Risk Information
      ↓
Gemini AI
      ↓
Structured Recommendation
      ↓
Dashboard
```

The system is designed with fallback behaviour:

```text
Gemini Available
       ↓
AI Recommendation

Gemini Unavailable
       ↓
Rule-Based Recommendation
```

This allows the dashboard to continue functioning even when the external AI service is unavailable.

---

# 📈 5. Short-Term Heat Forecast

HeatShield AI uses available weather forecast information to estimate how heat-risk conditions may change over the next **1–48 hours**.

The forecast interface can help visualize:

* Current conditions
* Future risk trend
* Expected changes
* Forecast uncertainty

The forecasting pipeline combines weather information with the heat-risk model.

---

# 🔎 6. Explainable Heat Risk

Instead of showing only a single risk number, the system attempts to provide context about the factors contributing to the estimate.

Potential factors include:

* 🌳 Vegetation
* 🏢 Built-up area
* 🛣️ Road density
* 💧 Water proximity
* 🌡️ Temperature
* 💨 Wind
* 💧 Humidity

This makes the dashboard easier to understand and inspect.

---

# 🚨 7. Hotspot Detection

The application identifies potentially important heat zones using zone-level risk information and feature differences.

Hotspot detection helps prioritize areas that may require closer inspection.

The dashboard can highlight these zones so users do not have to manually inspect every location.

---

# 📊 8. Historical Trends

HeatShield AI stores runtime history to visualize changes in system conditions.

Historical information can be used to observe:

* Risk changes
* Temperature trends
* System behaviour
* Previous dashboard states

The current history system is designed for prototype and demonstration purposes.

---

# ⚡ 9. Real-Time Updates

The backend supports WebSocket-based live updates.

```text
/ws/live
```

This allows the dashboard to receive updated application state without requiring a complete page refresh.

---

# 🧪 10. Automated Testing

The project includes automated tests covering important parts of the application.

Testing areas include:

* API behaviour
* Machine-learning model
* Recommendation engine
* Application state
* System status

### Current test suite

```text
68 automated tests
```

---

# 🧠 System Architecture

```text
                         ┌───────────────────────┐
                         │      Open-Meteo       │
                         │    Weather Service    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    FastAPI Backend    │
                         └───────────┬───────────┘
                                     │
             ┌───────────────────────┼───────────────────────┐
             │                       │                       │
             ▼                       ▼                       ▼
      Weather Service         ML Risk Model          State Management
             │                       │                       │
             │                       ├───────────────┐       │
             │                       │               │       │
             ▼                       ▼               ▼       ▼
       Live Weather           Risk Prediction   Hotspots   History
                                     │
                                     ▼
                              Forecasting
                                     │
                                     ▼
                           Explainable Factors
                                     │
                                     ▼
                            AI Recommendation
                                     │
                                     ▼
                              Gemini / Rules
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    Web Dashboard      │
                         │                       │
                         │ HTML / CSS / JS       │
                         │ Leaflet / Chart.js    │
                         └───────────────────────┘
```

---

# 🔄 Data → Intelligence → Action

The complete processing flow can be summarized as:

```text
┌──────────────────┐
│ Environmental    │
│ Data             │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Zone Features    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ML Risk Model    │
└────────┬─────────┘
         │
         ├───────────────► Heat Risk Score
         │
         ├───────────────► Hotspot Detection
         │
         ├───────────────► Forecast
         │
         └───────────────► Risk Factors
                                  │
                                  ▼
                         ┌────────────────┐
                         │ Gemini / Rules │
                         └───────┬────────┘
                                 │
                                 ▼
                      Actionable Suggestions
```

---

# 🛠️ Technology Stack

| Layer                   | Technology              |
| ----------------------- | ----------------------- |
| Frontend                | HTML5, CSS3, JavaScript |
| Backend                 | Python, FastAPI         |
| Machine Learning        | scikit-learn            |
| Data Processing         | Pandas, NumPy           |
| Maps                    | Leaflet                 |
| Charts                  | Chart.js                |
| Weather                 | Open-Meteo              |
| Generative AI           | Google Gemini           |
| Database                | SQLite                  |
| Model Storage           | Joblib                  |
| Real-Time Communication | WebSocket               |
| Testing                 | Pytest                  |
| Containerization        | Docker                  |
| Version Control         | Git                     |

---

# 📁 Project Structure

```text
heatshield-ai/
│
├── backend/
│   │
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
│   │
│   ├── media/
│   │   ├── awareness.mp4
│   │   ├── awareness.webm
│   │   ├── bg-city.jpg
│   │   ├── map-base.jpg
│   │   └── poster.jpg
│   │
│   └── vendor/
│       ├── chart.umd.js
│       └── leaflet/
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
│   ├── CHANGELOG.md
│   └── screenshots/
│       ├── dashboard-overview.png
│       ├── zone-analysis.png
│       └── ai-recommendations.png
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

## 1. Clone the Repository

```bash
git clone https://github.com/kanak-verma-developer/heatshield-ai.git
```

```bash
cd heatshield-ai
```

---

## 2. Create Virtual Environment

### Windows

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```powershell
pip install -r backend/requirements.txt
```

For development and testing:

```powershell
pip install -r backend/requirements-dev.txt
```

---

## 4. Configure Gemini AI

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
HEATSHIELD_LLM_PROVIDER=gemini
```

The API key is loaded through the backend and is **not exposed in the frontend**.

Never commit the `.env` file.

---

## 5. Start the Backend

```powershell
uvicorn backend.main:app --reload --port 8000
```

Then open:

```text
http://localhost:8000/
```

---

# 🧪 Run Tests

Run the complete test suite:

```powershell
pytest tests/ -v
```

Current repository:

```text
68 automated tests
```

---

# 🐳 Docker

Build the image:

```powershell
docker build -t heatshield-ai .
```

Run the application:

```powershell
docker run -p 8000:8000 heatshield-ai
```

The application will then be available locally on port `8000`.

---

# 📡 API Overview

The FastAPI backend provides endpoints for:

```text
Weather
   │
   ├── Current conditions
   └── Forecast
       
Zones
   │
   ├── Zone information
   └── Heat-risk analysis

Recommendations
   │
   └── AI / Rule-based suggestions

History
   │
   └── Historical observations

System
   │
   └── Health / status information

WebSocket
   │
   └── Live dashboard updates
```

Interactive API documentation is available through the running FastAPI application.

---

# 📊 Data Transparency

HeatShield AI intentionally separates **live**, **estimated**, **synthetic**, and **unavailable** data.

| Component                | Status                  |
| ------------------------ | ----------------------- |
| Current weather          | 🟢 LIVE                 |
| Hourly forecast          | 🟢 LIVE                 |
| Historical runtime data  | 🟢 WORKING              |
| ML pipeline              | 🟢 WORKING              |
| Gemini recommendations   | 🟢 LIVE when configured |
| Zone land-cover features | 🟡 ESTIMATE             |
| Surface temperature      | 🟡 ESTIMATE             |
| Zone coordinates         | 🟡 APPROXIMATE          |
| ML training dataset      | 🟠 SYNTHETIC            |
| Satellite data           | ⚪ NOT CONNECTED         |
| IoT sensors              | ⚪ NOT CONNECTED         |

---

# 🤖 Machine Learning

The project includes a complete machine-learning pipeline.

### Current pipeline

```text
Synthetic Dataset
       ↓
Feature Preparation
       ↓
Train / Validation
       ↓
Model Training
       ↓
Model Evaluation
       ↓
Model Serialization
       ↓
Dashboard Prediction
```

The trained model is stored using Joblib and can be loaded by the backend.

---

## ⚠️ ML Limitation

The current model is trained using **synthetic data**.

Therefore, metrics obtained from this dataset represent model behaviour on the synthetic training/evaluation setup.

They **do not represent validated real-world prediction accuracy**.

Real-world deployment would require:

* Historical temperature measurements
* Land-surface temperature
* Reliable land-cover information
* Ground observations
* Satellite-derived features
* Seasonal datasets
* Proper validation across different locations and time periods

---

# 🛰️ Current Data Limitations

Some components are intentionally marked as estimates because reliable external datasets have not yet been integrated.

### Current prototype

```text
Live Weather
      +
Estimated Zone Features
      +
Synthetic ML Training Data
      +
Forecast Data
      +
AI Recommendations
```

### Future production system

```text
Live Weather
      +
Satellite Data
      +
GIS Boundaries
      +
IoT Sensors
      +
Historical Ground Data
      +
Validated ML Model
      +
AI Recommendations
```

This distinction is important because the current application is an **AI/ML prototype**, not an official municipal heat-monitoring system.

---

# 🔐 Security

HeatShield AI follows basic API-key security practices.

* API keys are stored in environment variables.
* `.env` is excluded from Git.
* Gemini keys are not placed inside frontend JavaScript.
* `.env.example` contains placeholders only.
* Secrets are not intentionally included in the repository.

---

# 🌱 Future Roadmap

## 🛰️ Environmental Data

* [ ] Integrate satellite-derived land-surface temperature
* [ ] Add Sentinel/Landsat environmental features
* [ ] Replace estimated land-cover values with measured datasets
* [ ] Add official GIS zone boundaries
* [ ] Add historical environmental datasets

---

## 🧠 Machine Learning

* [ ] Train using real-world datasets
* [ ] Improve model calibration
* [ ] Add uncertainty-aware predictions
* [ ] Improve seasonal modelling
* [ ] Validate predictions against ground observations
* [ ] Explore advanced forecasting models

---

## 📡 IoT Integration

Future versions can integrate physical environmental sensors for:

* Temperature
* Humidity
* Air quality
* Noise
* Light
* Other environmental indicators

This would allow the platform to combine:

```text
Satellite
   +
Weather
   +
IoT
   +
ML
   +
AI
```

---

## 🖥️ Platform Improvements

* [ ] User authentication
* [ ] Personalized dashboards
* [ ] Heat alerts
* [ ] Notification system
* [ ] City-level scalability
* [ ] Production deployment
* [ ] Monitoring and observability
* [ ] Advanced analytics

---

# 💡 Project Highlights

HeatShield AI demonstrates the integration of multiple technologies into a single working application.

### Full-Stack Development

```text
Frontend
   ↕
REST API
   ↕
Backend Services
   ↕
ML Pipeline
   ↕
Data
```

### AI Integration

```text
Application Data
      ↓
Context Generation
      ↓
Gemini
      ↓
Structured Response
      ↓
Dashboard
```

### Real-Time Architecture

```text
Backend State
      ↓
WebSocket
      ↓
Live Dashboard
```

---

# 🎯 What This Project Demonstrates

This project brings together:

* Full-stack web development
* REST API development
* FastAPI
* Machine learning
* Data processing
* Environmental data analysis
* Interactive maps
* Data visualization
* Forecasting
* Generative AI
* WebSockets
* SQLite
* Automated testing
* Docker
* Git/GitHub
* API integration
* Security-aware configuration

---

# 🌍 Project Vision

Urban heat is influenced by multiple environmental and structural factors.

HeatShield AI explores how these different data sources can be brought together into a single interface that makes heat-related information easier to understand.

The long-term vision is to move from a prototype using estimated and synthetic inputs toward a system supported by:

```text
Real Environmental Data
        +
Satellite Observations
        +
Ground Sensors
        +
Historical Records
        +
Machine Learning
        +
Generative AI
```

The current project provides the foundation for that direction while clearly identifying which components are already working and which still require real-world data integration.

---

# 👩‍💻 Built By

## Kanak Verma

**B.Tech — Computer Science & Engineering (Data Science)**

**Focus Areas**

```text
Full-Stack Development
AI / Machine Learning
Data-Driven Applications
Environmental Intelligence
```

Moradabad, Uttar Pradesh, India

---

# ⭐ Repository

If you find **HeatShield AI** interesting, you can explore the complete source code here:

**GitHub Repository**

https://github.com/kanak-verma-developer/heatshield-ai

---

## 🔥 HeatShield AI

> **From environmental data to intelligent heat-risk insights.**
