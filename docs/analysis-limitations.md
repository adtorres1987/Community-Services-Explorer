# Analysis limitations

The proximity analysis answers a narrow question: *what share of each
community's residents, and of its area, lies within a straight-line radius of
a public school, a public library or a transit stop?* It is easy to read more into the result than it supports.
These are the known limitations.

## What the radius does not measure

- **Straight-line distance, not travel.** A 1 km radius can cross freeways
  (I-10, I-215), rail lines, the Santa Ana River and washes that make the real
  walk much longer. Measuring access would need a street network and travel
  times (roadmap Phase 8).
- **Proximity is not access.** The analysis ignores enrolment boundaries,
  school choice, capacity, grade levels served, transport and quality.
  A school nearby may not be one a given student can attend; a library nearby
  may be open few hours.
- **School-age is by age only.** "Ages 5–17" counts residents of that age
  (2020 DHC), not enrolled students: it includes children who are home-schooled
  or attend private schools, and excludes pre-kindergarten. All residents
  (`POP100`) remain available.

## Population estimate

- **Area apportionment.** Residents are 2020 census block counts. When a
  coverage area (or a 2026 boundary) cuts a block, the block's population is
  split in proportion to area, assuming people are spread evenly within it.
  Small urban blocks make this accurate in built-up areas; large blocks on the
  urban edge (foothills, washes) can be off.
- **Different years.** Population is from 2020, boundaries from 2026 and
  schools from 2025–26. Growth and annexations since 2020 are not reflected.
- **Ages 5–17 date faster than totals.** The 2020 children are 11–23 in 2026;
  the share near schools describes where school-age children lived in 2020,
  which is a reasonable proxy for where families live, not a current count.
- **Noise in block age counts.** 2020 Census counts include
  disclosure-avoidance noise. A single block's age count can be off by a few
  people; sums over a community (thousands of blocks) are reliable, single
  blocks are not, which is why the app never shows them.
- **Simplified blocks.** Block geometry is simplified with a 1 m tolerance
  after the population is computed (total area changes by ~0.003 %).
- **Area vs. people.** Both are reported because they diverge: in Redlands,
  40 % of the land but 75 % of residents are within 1 km of a school; the
  remaining land is largely hills and open space.
- **Children live closer to schools.** At 1 km, 84.2 % of residents aged 5–17
  are near a school versus 81.8 % of all residents, and the share is higher
  in every community; both measures are shown so the gap is visible.

## Data choices that affect the numbers

- **Assignment by boundary.** A school belongs to the place whose boundary
  contains it, not to its mailing-address city. 15 schools have an address
  city different from their place (e.g. Mission Elementary, "Redlands", is in
  Loma Linda).
- **Neighbouring schools count.** Coverage uses every eligible school within
  the radius, including schools in other study places and 32 context schools
  up to 2 km outside the study area (Fontana, Bloomington, unincorporated San
  Bernardino, Riverside County, Calimesa). Schools farther away cannot reach
  inside within the 2 km maximum radius, so there is no edge effect.
- **Exclusively virtual schools are excluded** from coverage (`Virtual = 'V'`,
  7 records). Their location is an administrative office; three share one point.
- **Co-located schools.** Some records share a site (0–4 m apart). School
  counts are of records, not physical sites.
- **Mentone is a CDP**, a statistical area defined by the Census Bureau, not a
  city with legal limits.
- **Public schools only.** Private schools, preschools and colleges are not in
  the CDE dataset.
- **Libraries: fixed public outlets only.** Central and branch libraries of
  public library systems count; bookmobiles, county law libraries, school and
  academic libraries do not. A small branch open 1,008 hours a year counts the
  same as a 64,000 sq ft central library: size and hours are shown in the
  popup but do not weight the coverage.
- **Library radii are in miles** (½, 1, 2 miles, rounded to 800 m, 1.6 km and
  3.2 km), as is usual in US library planning; they are not comparable with
  the school radii. Libraries up to 3.2 km outside the study area count, so
  there is no edge effect at the largest radius either.
- **Transit: a stop nearby is not a useful trip.** Coverage says a stop is
  within walking distance, not that its routes go where people need to go.
  "Any stop" includes stops with one bus an hour; the frequent-bus filter
  (4+ departures per hour at the stop, 7–9 am) is the stricter measure. The
  service level counts all routes and both directions at a stop, so a stop
  served by two hourly routes counts as two departures per hour.
- **Transit: one weekday, one schedule version.** Service is measured on
  Wednesday 16 September 2026 from the autumn 2026 schedules; weekends,
  evenings and later service changes differ. Stops are boarding points, so
  both sides of a street are usually two stops.
- **Transit: Omnitrans and Metrolink only.** Other operators that reach the
  edges of the study area (e.g. Riverside Transit Agency, Mountain Transit)
  and OmniRide demand-responsive service are not included.

## Source and method details

- **Snapshot in time.** Sources were downloaded between 2026-11-02 and
  2026-11-18 (library data are for fiscal year 2024, transit schedules for
  autumn 2026);
  `scripts/download_data.py` detects later changes by checksum.
- **TIGER/Line boundaries are cartographic,** intended for statistical use,
  not legal boundary determination.
- **Projection.** Distances and areas are computed in EPSG:26911
  (NAD83 / UTM zone 11N). At this scale projected and geodesic distances agree
  to the metre (verified in `database/sql/spatial_queries.sql`).
- **Buffer approximation.** PostGIS approximates circles with 32-segment
  polygons; an independent GeoPandas calculation with the same resolution
  gives identical results.
