import { describe, expect, it } from 'vitest'
import { closestRadius, radiusOption, SERVICES } from './services'

describe('closestRadius', () => {
  it('keeps the coverage off when it was off', () => {
    expect(closestRadius(null, SERVICES.library)).toBeNull()
  })

  it('picks the closest radius of the new service', () => {
    expect(closestRadius(1000, SERVICES.library)).toBe(800)
    expect(closestRadius(2000, SERVICES.library)).toBe(1600)
    expect(closestRadius(3200, SERVICES.school)).toBe(2000)
    expect(closestRadius(800, SERVICES.school)).toBe(1000)
  })
})

describe('radiusOption', () => {
  it('uses the service labels', () => {
    expect(radiusOption(SERVICES.library, 1600)).toEqual({ value: 1600, label: '1 mi', long: '1 mile (1.6 km)' })
    expect(radiusOption(SERVICES.school, 1500).label).toBe('1.5 km')
  })

  it('falls back to metres for an unlisted radius', () => {
    expect(radiusOption(SERVICES.school, 750).long).toBe('750 m')
  })
})

describe('service colours', () => {
  it('colours library outlets by type', () => {
    expect(SERVICES.library.color('Central')).not.toBe(SERVICES.library.color('Branch'))
    expect(SERVICES.library.excluded).toBeUndefined()
  })
})
