from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg import OperationalError
from psycopg_pool import PoolTimeout

from app.api import analysis, cities, facilities, health
from app.config import CORS_ORIGINS, database_conninfo
from app.db import create_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = create_pool(database_conninfo())
    # Don't block startup: requests return 503 while the database is unreachable
    pool.open(wait=False)
    app.state.pool = pool
    yield
    pool.close()


app = FastAPI(
    title="Community Services Explorer API",
    version="0.1.0",
    description=(
        "Public schools in Redlands and Yucaipa, California. Geometries are "
        "GeoJSON in EPSG:4326; distances are straight-line metres computed in EPSG:26911."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(PoolTimeout)
@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


app.include_router(health.router)
app.include_router(facilities.router)
app.include_router(cities.router)
app.include_router(analysis.router)
