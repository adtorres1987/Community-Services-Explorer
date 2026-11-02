# One-shot job: loads data/processed/study_area.gpkg into PostGIS, then exits.
FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/load_postgis.py scripts/
COPY data/processed/study_area.gpkg data/processed/

USER nobody
CMD ["python", "scripts/load_postgis.py"]
