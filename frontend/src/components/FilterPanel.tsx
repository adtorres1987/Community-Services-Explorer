import type { CityProperties } from '../services/api'

interface Props {
  places: CityProperties[]
  subtypes: string[]
  /** Selected places; empty means all */
  cities: string[]
  subtype: string | null
  radius: number | null
  onCitiesChange: (cities: string[]) => void
  onSubtypeChange: (subtype: string | null) => void
  onRadiusChange: (radius: number | null) => void
}

const RADIUS_OPTIONS: { value: number | null; label: string }[] = [
  { value: null, label: 'Off' },
  { value: 500, label: '500 m' },
  { value: 1000, label: '1 km' },
  { value: 1500, label: '1.5 km' },
  { value: 2000, label: '2 km' },
]

export function FilterPanel({
  places,
  subtypes,
  cities,
  subtype,
  radius,
  onCitiesChange,
  onSubtypeChange,
  onRadiusChange,
}: Props) {
  const names = places.map((p) => p.name)

  function toggle(name: string, checked: boolean) {
    const next = checked ? [...cities, name] : cities.filter((c) => c !== name)
    // Keep the list order so the statistics table stays stable
    onCitiesChange(names.filter((n) => next.includes(n)))
  }

  return (
    <section className="panel" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filters</h2>

      <fieldset className="field">
        <legend>Communities</legend>
        <div className="checklist">
          {places.map((place) => (
            <label key={place.name}>
              <input
                type="checkbox"
                checked={cities.includes(place.name)}
                onChange={(e) => toggle(place.name, e.target.checked)}
              />
              <span>
                {place.name}
                {place.place_type === 'CDP' && <span className="tag">CDP</span>}
              </span>
            </label>
          ))}
        </div>
        <div className="checklist__footer">
          <p className="hint">
            {cities.length === 0 || cities.length === names.length
              ? 'Showing all communities.'
              : `${cities.length} of ${names.length} selected.`}
          </p>
          <div className="checklist__actions">
            <button type="button" onClick={() => onCitiesChange(names)}>
              All
            </button>
            <button type="button" onClick={() => onCitiesChange([])} disabled={cities.length === 0}>
              None
            </button>
          </div>
        </div>
      </fieldset>

      <label className="field">
        <span>School type</span>
        <select value={subtype ?? ''} onChange={(e) => onSubtypeChange(e.target.value || null)}>
          <option value="">All types</option>
          {subtypes.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="field">
        <legend>Proximity radius</legend>
        <div className="segmented">
          {RADIUS_OPTIONS.map((option) => (
            <label key={option.label}>
              <input
                type="radio"
                name="radius"
                checked={radius === option.value}
                onChange={() => onRadiusChange(option.value)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </section>
  )
}
