import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { CityProximity, ProximityResponse } from '../services/api'
import type { RequestState } from '../services/useRequest'
import { makeFacility, makePlace } from '../test/fixtures'
import { StatisticsPanel } from './StatisticsPanel'

const places = [
  makePlace('Mentone', { place_type: 'CDP', population: 9557 }),
  makePlace('Redlands', { population: 73161 }),
]

const facilities = [
  makeFacility({ id: 1, city: 'Redlands' }),
  makeFacility({ id: 2, city: 'Redlands' }),
  makeFacility({ id: 3, city: 'Mentone' }),
]

function idle(overrides: Partial<RequestState<ProximityResponse>> = {}) {
  return { data: undefined, error: undefined, loading: false, retry: vi.fn(), ...overrides }
}

function result(overrides: Partial<CityProximity>): CityProximity {
  return {
    city: 'Redlands',
    eligible_facilities: 18,
    excluded_facilities: 4,
    contributing_facilities: 22,
    city_area_km2: 93.86,
    covered_area_km2: 37.17,
    covered_pct: 39.6,
    population: 73161,
    covered_population: 54741,
    covered_population_pct: 74.8,
    coverage: null,
    ...overrides,
  }
}

const proximity: ProximityResponse = {
  radius_m: 1000,
  facility_type: 'school',
  facility_subtype: null,
  method: 'Straight-line',
  results: [
    result({
      city: 'Mentone',
      eligible_facilities: 2,
      excluded_facilities: 0,
      contributing_facilities: 4,
      city_area_km2: 15.85,
      covered_area_km2: 4.77,
      covered_pct: 30.1,
      population: 9557,
      covered_population: 6589,
      covered_population_pct: 68.9,
    }),
    result({}),
  ],
}

function row(name: string | RegExp) {
  return within(screen.getByRole('row', { name }))
}

function cells(name: string | RegExp) {
  return row(name)
    .getAllByRole('cell')
    .map((c) => c.textContent)
}

describe('StatisticsPanel', () => {
  it('shows schools and population per place, with a total', () => {
    render(
      <StatisticsPanel
        places={places}
        selectedCity={null}
        subtype={null}
        facilities={facilities}
        radius={null}
        proximity={idle()}
      />,
    )
    expect(cells(/^Redlands/)).toEqual(['2', '73,161'])
    expect(cells(/^Mentone/)).toEqual(['1', '9,557'])
    expect(cells(/^All /)).toEqual(['3', '82,718'])
    expect(row(/^Mentone/).getByText('CDP')).toBeInTheDocument()
    expect(screen.queryByText(/Residents within/)).not.toBeInTheDocument()
    expect(screen.getByText(/straight-line distance/)).toBeInTheDocument()
  })

  it('shows population and area coverage for the radius', () => {
    render(
      <StatisticsPanel
        places={places}
        selectedCity="Redlands"
        subtype={null}
        facilities={facilities}
        radius={1000}
        proximity={idle({ data: proximity })}
      />,
    )
    expect(screen.getByRole('columnheader', { name: 'Residents within 1 km' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Area within 1 km' })).toBeInTheDocument()
    expect(cells(/^Redlands/)).toEqual(['2', '74.8%', '39.6%'])
    expect(cells(/^Mentone/)).toEqual(['1', '68.9%', '30.1%'])
    // Totals are weighted by population and area, not averaged
    // (54,741 + 6,589) / (73,161 + 9,557) and (37.17 + 4.77) / (93.86 + 15.85)
    expect(cells(/^All /)).toEqual(['3', '74.1%', '38.2%'])
    expect(
      screen.getByText(/54,741 of 73,161 residents and 37.17 of 93.86 km² are within 1 km/),
    ).toBeInTheDocument()
    expect(screen.getByText(/including 4 outside Redlands; 4 exclusively virtual excluded/)).toBeInTheDocument()
  })

  it('reports analysis errors with a retry button', async () => {
    const state = idle({ error: 'Database unavailable' })
    render(
      <StatisticsPanel
        places={places}
        selectedCity={null}
        subtype={null}
        facilities={facilities}
        radius={500}
        proximity={state}
      />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Database unavailable')
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(state.retry).toHaveBeenCalledOnce()
  })
})
