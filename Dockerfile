# HeatShield AI -- containerized deployment (API + dashboard on one port).
#
# Build:  docker build -t heatshield-ai .
# Run:    docker run -p 8000:8000 heatshield-ai
# Open:   http://localhost:8000/        (dashboard is served by the backend)
#
# Optional:  -e ANTHROPIC_API_KEY=...  -e ALLOWED_ORIGINS=https://your.site
#            -v heatshield-data:/app/data   (persist risk history)
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY data/ data/
COPY ml/ ml/
COPY frontend/ frontend/

# Train at build time only if no pre-trained model is shipped, so the saved
# model always matches the scikit-learn version installed in the image.
RUN if [ ! -f backend/models/heat_risk_model.joblib ]; then \
      python ml/generate_dataset.py && python ml/train.py ; \
    fi

RUN useradd --create-home appuser && chown -R appuser /app/data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
