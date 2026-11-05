-- Study area: six places assigned by boundary (not by address city), schools near
-- the study area kept for coverage only, and census block population.

BEGIN;

-- facilities.city is now the study place whose boundary contains the facility,
-- NULL for context facilities outside the study area.
ALTER TABLE facilities RENAME COLUMN in_city_limits TO in_study_area;
ALTER TABLE facilities ALTER COLUMN city DROP NOT NULL;
ALTER TABLE facilities ADD COLUMN address_city TEXT;

-- Convert rows loaded with the previous meaning; scripts/load_postgis.py replaces them
UPDATE facilities SET address_city = city;
UPDATE facilities SET city = NULL WHERE NOT in_study_area;

ALTER TABLE facilities
    ADD CONSTRAINT facilities_study_area_city_chk CHECK (in_study_area = (city IS NOT NULL));

ALTER TABLE city_boundaries ADD COLUMN place_type TEXT;  -- 'city' or 'CDP'
ALTER TABLE city_boundaries ADD COLUMN population INTEGER;

-- 2020 census blocks clipped to each study place; population apportioned by area
CREATE TABLE population_units (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geoid20     TEXT NOT NULL,
    city        TEXT NOT NULL REFERENCES city_boundaries (name) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    population  DOUBLE PRECISION NOT NULL,
    geom        geometry(MultiPolygon, 26911) NOT NULL
);

CREATE INDEX population_units_geom_idx
ON population_units
USING GIST (geom);

CREATE INDEX population_units_city_idx
ON population_units (city);

COMMIT;
