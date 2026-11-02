from typing import Annotated

from fastapi import APIRouter, Depends
from psycopg import Connection

from app.db import get_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health(conn: Annotated[Connection, Depends(get_connection)]) -> dict[str, str]:
    """API and database status. Returns 503 if the database is unreachable."""
    row = conn.execute("SELECT postgis_lib_version() AS postgis").fetchone()
    return {"status": "ok", "database": "ok", "postgis": row["postgis"]}
