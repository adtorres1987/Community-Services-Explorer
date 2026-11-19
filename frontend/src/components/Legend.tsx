import type { ServiceConfig } from '../features/facilities/services'
import { BOUNDARY_STYLE, COVERAGE_STYLE } from '../maps/basemap'

export function Legend({ service }: { service: ServiceConfig }) {
  return (
    <section className="panel" aria-labelledby="legend-heading">
      <h2 id="legend-heading">Legend</h2>
      <ul className="legend">
        {service.categories.map((category) => (
          <li key={category.name}>
            <span className="swatch swatch--dot" style={{ background: category.color }} />
            {category.name}
          </li>
        ))}
        {service.excluded && (
          <li>
            <span className="swatch swatch--dot swatch--hollow" />
            {service.excluded.legend}
          </li>
        )}
        <li>
          <span className="swatch swatch--dot swatch--faded" />
          Other community or outside the study area (still counts toward coverage)
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
          Community boundaries (TIGER/Line 2026)
        </li>
      </ul>
    </section>
  )
}
