# HeatShield AI
### AI-Powered Urban Heat Intelligence & Mitigation Dashboard

HeatShield AI is a full-stack web application that combines live weather data, machine learning, zone-level analysis, heat-risk assessment, forecasting, and AI-assisted recommendations to help users understand urban heat conditions.

The project currently supports Moradabad and Delhi through an interactive dashboard featuring city selection, weather information, representative zone analysis, heat-safety guidance, and forecasts.

## Key Features

### Live Weather Monitoring
- Current temperature, humidity, and wind conditions
- Weather forecast information
- City selection for Moradabad and Delhi
- Backend-powered dashboard updates

### Zone-Level Heat Analysis
- Multiple representative zones for supported cities
- Zone-wise temperature estimates and heat-risk visualization
- Identification of comparatively warmer areas
- Environmental adjustments based on configured zone characteristics

**Data note:** Zone-level temperatures are estimates based on weather data and configured environmental indicators. They are not direct measurements from individual neighbourhoods.

### Heat-Risk Assessment
- Machine-learning-based risk analysis
- Risk-level visualization
- Environmental indicators
- Comparative hotspot identification

### Weather Forecasting
- Hourly weather information
- Short-term forecast views
- Identification of comparatively warmer and cooler periods

### AI-Assisted Recommendations
- Context-aware heat-safety guidance
- Gemini API integration when configured
- Rule-based fallback recommendations when AI services are unavailable

### Public Heat-Safety Information
- Guidance for vulnerable groups and outdoor workers
- Heatstroke warning signs and safety guidance
- Emergency-response information

### Interactive Dashboard
- Responsive web interface
- Hindi and English language options
- Interactive heat-map and zone selection
- Weather, forecasts, safety tips, and recommendations

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI, Uvicorn |
| Weather Data | Open-Meteo |
| Machine Learning | Pandas, NumPy, Scikit-learn, Joblib |
| AI Recommendations | Gemini API, rule-based fallback |
| Visualization | Leaflet, Chart.js |
| Storage | SQLite |
| Deployment | Docker, Render |
| Version Control | Git, GitHub |

## Project Structure

```text
heatshield-ai/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── models/
│   └── services/
├── data/
│   └── zones.py
├── docs/
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── area3d.js
│   ├── media/
│   └── vendor/
├── ml/
├── tests/
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

## Run Locally

### 1. Get the Project

Obtain the project source code and open its root directory in a terminal.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file using `.env.example` as a reference. Add your own API key if AI-powered recommendations are required.

```env
GEMINI_API_KEY=YOUR_API_KEY
HEATSHIELD_LLM_PROVIDER=gemini
```

Never commit the `.env` file or expose private credentials.

### 5. Start the Backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

If running from inside the `backend` directory:

```bash
python -m uvicorn main:app --reload --port 8000
```

The interactive API documentation is available through the local FastAPI server's `/docs` endpoint.

## Testing

Install development dependencies:

```bash
pip install -r backend/requirements-dev.txt
```

Run tests from the project root:

```bash
pytest
```

## Docker

Build the image:

```bash
docker build -t heatshield-ai .
```

Run the container:

```bash
docker run -p 8000:8000 heatshield-ai
```

Configure required environment variables securely when running the container.

## Data Transparency and Limitations

HeatShield AI is a prototype and engineering project. Results should be interpreted according to the source and maturity of each data component.

| Data Component | Status |
|---|---|
| Current weather | Retrieved from Open-Meteo |
| Weather forecast | Retrieved from available forecast data |
| Zone definitions | Representative prototype zones |
| Zone-level temperature | Estimated using weather data and configured adjustments |
| Land-cover indicators | Configured estimates |
| Machine-learning training data | Synthetic prototype data |
| Satellite-derived surface temperature | Not currently integrated |
| Physical IoT sensor network | Not currently connected |
| Real-world model validation | Requires additional measured datasets |

Synthetic training data and estimated zone indicators do not establish validated real-world neighbourhood-level prediction accuracy. Weather values may vary with location, forecast updates, and data availability.

## Security

- Store API keys in environment variables.
- Keep `.env` excluded from version control.
- Never publish passwords, tokens, or private credentials.
- Configure production secrets through the deployment platform.
- Review logs and dependencies before production use.

## Future Roadmap

### Data Improvements
- Satellite-derived land-surface temperature
- NDVI and improved land-cover information
- Higher-resolution spatial data
- Validation against measured environmental datasets

### IoT Integration
- ESP32 sensor nodes
- Local temperature and humidity monitoring
- Air-quality and noise sensing
- Real-time environmental telemetry

### Advanced Intelligence
- Improved forecasting
- Validation with real-world observations
- Spatial anomaly detection
- Community-level heat alerts

## Project Status

**Status: Prototype — Deployed**

HeatShield AI demonstrates how live weather information, machine learning, zone-level estimates, forecasting, and AI-assisted guidance can be combined in an interactive urban heat dashboard.

The long-term goal is to improve spatial accuracy through validated datasets, satellite information, and real sensor measurements.

## Author

**Kanak Verma**  
B.Tech — Computer Science & Engineering (Data Science)

Interests: Web Development, Machine Learning, Environmental Data, and Practical Technology Solutions.
