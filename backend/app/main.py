from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
        "Public schools, public libraries and transit stops in nine San Bernardino Valley communities "
        "(Colton, Grand Terrace, Highland, Loma Linda, Mentone, Redlands, Rialto, "
        "San Bernardino, Yucaipa), California, with proximity coverage by area and "
        "2020 population (total and aged 5-17). "
        "Geometries are GeoJSON in EPSG:4326; distances are straight-line metres "
        "computed in EPSG:26911."
    ),
    lifespan=lifespan,
)

# GeoJSON compresses well: /facilities shrinks from ~690 KB to ~100 KB
app.add_middleware(GZipMiddleware, minimum_size=1000)
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
