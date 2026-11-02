from typing import Literal

from pydantic import BaseModel

from app.schemas.geojson import Geometry


class CityProperties(BaseModel):
    name: str
    geoid: str
    area_km2: float
    facility_count: int  # facilities whose address city matches


class CityFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: Geometry
    properties: CityProperties


class CityCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[CityFeature]
