from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.geojson import Geometry


class FacilityProperties(BaseModel):
    id: int
    name: str
    facility_type: str
    facility_subtype: str | None
    city: str | None  # study place containing the facility; None outside the study area
    address_city: str | None  # mailing-address city from the source
    in_study_area: bool  # False: nearby facility used only for proximity coverage
    proximity_eligible: bool
    attributes: dict[str, Any]


class FacilityFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: int
    geometry: Geometry
    properties: FacilityProperties


class FacilityCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[FacilityFeature]
