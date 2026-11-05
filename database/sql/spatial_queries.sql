-- Spatial queries for the study area (six places; see docs/database.md). Run with:
--   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < database/sql/spatial_queries.sql
-- Geometries are in EPSG:26911, so ST_Distance / ST_DWithin / ST_Buffer use metres.
-- Distances are straight-line, not street-network distances.

\echo '1. Geometry columns and SRID'
SELECT f_table_name, f_geometry_column, type, srid
FROM geometry_columns
ORDER BY f_table_name;

\echo '2. Spatial indexes'
SELECT tablename, indexname
FROM pg_indexes
WHERE indexdef ILIKE '%USING gist%'
ORDER BY tablename;

\echo '3. ST_Intersects: schools inside each place boundary vs the assigned city column'
SELECT
    b.name AS boundary,
    count(f.id) AS schools_inside,
    count(f.id) FILTER (WHERE f.city = b.name) AS assigned_to_place
FROM city_boundaries b
LEFT JOIN facilities f ON ST_Intersects(f.geom, b.geom)
GROUP BY b.name
ORDER BY b.name;

\echo '4. ST_Distance: context schools (outside the study area) and their distance to it'
SELECT
    f.name,
    f.address_city,
    round(min(ST_Distance(f.geom, b.geom))) AS distance_to_study_area_m
FROM facilities f
CROSS JOIN city_boundaries b
WHERE NOT f.in_study_area
GROUP BY f.id, f.name, f.address_city
ORDER BY distance_to_study_area_m
LIMIT 10;

\echo '5. ST_Distance: nearest proximity-eligible school (projected vs geodesic metres)'
SELECT
    f.name,
    nearest.name AS nearest_school,
    round(ST_Distance(f.geom, nearest.geom)) AS utm_m,
    round(ST_Distance(
        ST_Transform(f.geom, 4326)::geography,
        ST_Transform(nearest.geom, 4326)::geography
    )) AS geodesic_m
FROM facilities f
CROSS JOIN LATERAL (
    SELECT o.name, o.geom
    FROM facilities o
    WHERE o.id <> f.id AND o.proximity_eligible
    ORDER BY o.geom <-> f.geom
    LIMIT 1
) AS nearest
WHERE f.proximity_eligible
ORDER BY utm_m
LIMIT 5;

\echo '6. ST_DWithin + ST_Transform: eligible schools within 1 km of a WGS84 point (Redlands City Hall)'
WITH origin AS (
    SELECT ST_Transform(ST_SetSRID(ST_MakePoint(-117.1817, 34.0557), 4326), 26911) AS geom
)
SELECT f.name, round(ST_Distance(f.geom, origin.geom)) AS distance_m
FROM facilities f, origin
WHERE f.proximity_eligible
  AND ST_DWithin(f.geom, origin.geom, 1000)
ORDER BY distance_m;

\echo '7. ST_Buffer + ST_Union: share of each place area within 500 m and 1 km of any eligible school'
-- Schools in neighbouring places and context schools count too (same method as the API)
SELECT
    b.name AS place,
    r.radius_m,
    round((ST_Area(b.geom) / 1e6)::numeric, 2) AS place_km2,
    round((100 * ST_Area(ST_Intersection(
        b.geom,
        (SELECT ST_Union(ST_Buffer(f.geom, r.radius_m))
         FROM facilities f
         WHERE f.proximity_eligible AND ST_DWithin(f.geom, b.geom, r.radius_m))
    )) / ST_Area(b.geom))::numeric, 1) AS pct_area_within_radius
FROM city_boundaries b
CROSS JOIN (VALUES (500), (1000)) AS r(radius_m)
ORDER BY b.name, r.radius_m;

\echo '7b. Population: share of residents within 1 km (block population apportioned by area)'
WITH coverage AS (
    SELECT
        b.name,
        b.population,
        ST_Intersection(
            b.geom,
            (SELECT ST_Union(ST_Buffer(f.geom, 1000))
             FROM facilities f
             WHERE f.proximity_eligible AND ST_DWithin(f.geom, b.geom, 1000))
        ) AS geom
    FROM city_boundaries b
)
SELECT
    c.name AS place,
    c.population,
    round(sum(u.population * ST_Area(ST_Intersection(u.geom, c.geom)) / ST_Area(u.geom))) AS covered,
    round((100 * sum(u.population * ST_Area(ST_Intersection(u.geom, c.geom)) / ST_Area(u.geom))
        / c.population)::numeric, 1) AS pct_population_within_1km
FROM coverage c
JOIN population_units u ON u.city = c.name AND ST_Intersects(u.geom, c.geom)
GROUP BY c.name, c.population
ORDER BY c.name;

\echo '8. ST_Transform: GeoJSON output in EPSG:4326 (as the API will return it)'
SELECT name, ST_AsGeoJSON(ST_Transform(geom, 4326), 6) AS geojson
FROM facilities
ORDER BY name
LIMIT 2;
