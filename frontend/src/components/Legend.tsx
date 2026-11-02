import { CATEGORIES, CATEGORY_COLORS } from '../features/facilities/schools'
import { BOUNDARY_STYLE, COVERAGE_STYLE } from '../maps/basemap'

export function Legend() {
  return (
    <section className="panel" aria-labelledby="legend-heading">
      <h2 id="legend-heading">Legend</h2>
      <ul className="legend">
        {CATEGORIES.map((category) => (
          <li key={category}>
            <span className="swatch swatch--dot" style={{ background: CATEGORY_COLORS[category] }} />
            {category}
          </li>
        ))}
        <li>
          <span className="swatch swatch--dot swatch--hollow" />
          Exclusively virtual (not in proximity analysis)
        </li>
        <li>
          <span
            className="swatch swatch--area"
            style={{ background: COVERAGE_STYLE.fillColor, opacity: 0.45 }}
          />
          Area within the selected radius
        </li>
        <li>
          <span className="swatch swatch--line" style={{ borderColor: BOUNDARY_STYLE.color }} />
          City limits (TIGER/Line 2026)
        </li>
      </ul>
    </section>
  )
}
