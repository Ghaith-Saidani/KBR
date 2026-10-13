FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY data/models /app/data/models
COPY data/reports/anomaly_detection_report.json /app/data/reports/anomaly_detection_report.json
COPY data/reports/risk_scoring_report.json /app/data/reports/risk_scoring_report.json
COPY alembic.ini /app/alembic.ini

EXPOSE 8000

CMD ["sh", "-c", "alembic -c /app/alembic.ini upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
