# Development environment

Recorded on 2026-11-02 (Phase 0).

| Component | Version |
|---|---|
| macOS | 27.0.1 (Apple Silicon, arm64) |
| QGIS | 4.0.3 (used for inspection and visual validation only) |
| Git | 2.50.1 |
| Docker | 29.0.1 |
| Python | 3.14.5 (Homebrew, `/opt/homebrew/bin/python3.14`) |
| GDAL (bundled with pyogrio) | 3.12.4 |
| PROJ (bundled with pyproj) | 9.8.1 |
| Node.js / npm | 25.1.0 / 11.6.2 |
| PostgreSQL / PostGIS (Docker) | 17 / 3.5.3 (`imresamu/postgis:17-3.5`) |

Python package versions are pinned in `requirements.txt` (full development
environment) and `backend/requirements.txt` (API container). Frontend versions
are locked in `frontend/package-lock.json`. CI uses Python 3.14 and Node.js 24.

## Setup

```bash
/opt/homebrew/bin/python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Notes

- The system `python3` (`/usr/bin/python3`, 3.9.6) is too old for GeoPandas 1.x; create the virtual environment with Python 3.14, the version the pins were tested with.
- The project's Python environment is independent of the Python bundled with QGIS.
- QGIS project files saved with QGIS 4.x may not open in QGIS 3.x. Data (GeoPackage) and scripts are the source of truth, not the `.qgz` project.
