from typing import Literal

from pydantic import BaseModel

from app.schemas.geojson import Geometry


class CityProperties(BaseModel):
    name: str
    geoid: str
    place_type: str  # "city" or "CDP" (unincorporated census-designated place)
    area_km2: float
    population: int  # 2020 census, apportioned from blocks
    facility_count: int  # facilities inside the boundary


class CityFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: Geometry
    properties: CityProperties


class CityCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[CityFeature]
