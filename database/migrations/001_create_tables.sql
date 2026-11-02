-- Geometries are stored in EPSG:26911 (NAD83 / UTM zone 11N) so distances are in metres.
-- The API transforms to EPSG:4326 for GeoJSON output.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE city_boundaries (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geoid       TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    geom        geometry(MultiPolygon, 26911) NOT NULL
);

CREATE INDEX city_boundaries_geom_idx
ON city_boundaries
USING GIST (geom);

CREATE TABLE facilities (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id          TEXT NOT NULL,
    source_name        TEXT NOT NULL,
    name               TEXT NOT NULL,
    facility_type      TEXT NOT NULL,
    facility_subtype   TEXT,
    city               TEXT NOT NULL,  -- address city, not necessarily within city limits
    in_city_limits     BOOLEAN NOT NULL,
    proximity_eligible BOOLEAN NOT NULL,
    attributes         JSONB NOT NULL DEFAULT '{}',  -- source-specific fields
    geom               geometry(Point, 26911) NOT NULL,
    UNIQUE (source_name, source_id)
);

CREATE INDEX facilities_geom_idx
ON facilities
USING GIST (geom);

CREATE INDEX facilities_city_type_idx
ON facilities (city, facility_type);
