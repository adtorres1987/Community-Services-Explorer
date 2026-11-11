-- School-age population: residents aged 5-17 from the 2020 Census DHC (table P12),
-- by census block, apportioned by area like the total population.
-- NULL until scripts/load_postgis.py reloads the data.

BEGIN;

ALTER TABLE city_boundaries ADD COLUMN population_5_17 INTEGER;
ALTER TABLE population_units ADD COLUMN population_5_17 DOUBLE PRECISION;

COMMIT;
