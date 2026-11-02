from collections.abc import Iterator

from fastapi import Request
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def create_pool(conninfo: str) -> ConnectionPool:
    # timeout bounds how long a request waits for a connection when the database is down
    return ConnectionPool(
        conninfo,
        min_size=1,
        max_size=5,
        timeout=5,
        open=False,
        kwargs={"row_factory": dict_row},
    )


def get_connection(request: Request) -> Iterator[Connection]:
    with request.app.state.pool.connection() as conn:
        yield conn
