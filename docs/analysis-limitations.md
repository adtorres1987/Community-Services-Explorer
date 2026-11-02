# Analysis limitations

The proximity analysis answers one narrow question: *what share of each city's
area lies within a straight-line radius of a public school?* It is easy to read
more into the result than it supports. These are the known limitations.

## What the radius does not measure

- **Straight-line distance, not travel.** A 1 km radius can cross freeways,
  rail lines, washes and hills that make the real walk much longer. Measuring
  access would need a street network and travel times (roadmap Phase 8).
- **Area, not people.** Coverage is a share of land area. Parts of both cities
  are hills, parks or industrial land where no students live, so the
  percentage of *residents* near a school can differ substantially.
  Population-weighted coverage (e.g. with census blocks) would be the next step.
- **Proximity is not access.** The analysis ignores enrolment boundaries,
  school choice, capacity, grade levels served, transport and quality.
  A school nearby may not be one a given student can attend.

## Data choices that affect the numbers

- **Schools are selected by address city.** The CDE `City` field is a mailing
  address. Two schools with a Redlands address lie outside the Redlands city
  limits (Mission Elementary, 89 m; Redlands East Valley High, 772 m). They are
  kept and flagged with `in_city_limits = false`; their coverage is clipped to
  the city boundary.
- **Edge effect.** Only schools with a Redlands or Yucaipa address are loaded.
  Schools just across the boundary (Highland, Mentone, Loma Linda, Calimesa)
  are ignored, so coverage near the city edges is underestimated.
- **Exclusively virtual schools are excluded** from the proximity analysis
  (`Virtual = 'V'`, 4 records in Redlands). Their location is an administrative
  office; three of them share the same point.
- **Co-located schools.** Some records share a site (the two Gorman Learning
  Center records are 1 m apart; Green Valley High and Green Valley Independent
  Study are 4 m apart). Counts are of records, not physical sites.
- **Public schools only.** Private schools, preschools and colleges are not in
  the CDE dataset.

## Source and method details

- **Snapshot in time.** Schools: CDE California Public Schools 2025–26,
  downloaded 2026-11-02. Boundaries: Census TIGER/Line 2026. Both are
  updated periodically; `scripts/download_data.py` detects changes by checksum.
- **TIGER/Line boundaries are cartographic,** intended for statistical use,
  not legal boundary determination.
- **Projection.** Distances and areas are computed in EPSG:26911
  (NAD83 / UTM zone 11N). At this scale projected and geodesic distances agree
  to the metre (verified in `database/sql/spatial_queries.sql`).
- **Buffer approximation.** PostGIS approximates circles with 32-segment
  polygons, which gives results within 0.1 percentage points of a finer
  GeoPandas calculation.
