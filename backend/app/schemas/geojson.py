from typing import Any, Literal

from pydantic import BaseModel


class Geometry(BaseModel):
    """GeoJSON geometry in EPSG:4326 (longitude, latitude)."""

    type: Literal["Point", "Polygon", "MultiPolygon"]
    coordinates: list[Any]
