interface Props {
  cities: string[]
  subtypes: string[]
  city: string | null
  subtype: string | null
  radius: number | null
  onCityChange: (city: string | null) => void
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
  cities,
  subtypes,
  city,
  subtype,
  radius,
  onCityChange,
  onSubtypeChange,
  onRadiusChange,
}: Props) {
  return (
    <section className="panel" aria-labelledby="filters-heading">
      <h2 id="filters-heading">Filters</h2>

      <label className="field">
        <span>Community</span>
        <select value={city ?? ''} onChange={(e) => onCityChange(e.target.value || null)}>
          <option value="">All communities</option>
          {cities.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>

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
