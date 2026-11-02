import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { ProximityResponse } from '../services/api'
import type { RequestState } from '../services/useRequest'
import { makeFacility } from '../test/fixtures'
import { StatisticsPanel } from './StatisticsPanel'

const facilities = [
  makeFacility({ id: 1, city: 'Redlands' }),
  makeFacility({ id: 2, city: 'Redlands', in_city_limits: false }),
  makeFacility({ id: 3, city: 'Yucaipa' }),
]

function idle(overrides: Partial<RequestState<ProximityResponse>> = {}) {
  return { data: undefined, error: undefined, loading: false, retry: vi.fn(), ...overrides }
}

const proximity: ProximityResponse = {
  radius_m: 1000,
  facility_type: 'school',
  facility_subtype: null,
  method: 'Straight-line',
  results: [
    {
      city: 'Redlands',
      city_area_km2: 93.86,
      eligible_facilities: 20,
      excluded_facilities: 4,
      covered_area_km2: 36.38,
      covered_pct: 38.8,
      coverage: null,
    },
    {
      city: 'Yucaipa',
      city_area_km2: 73.13,
      eligible_facilities: 13,
      excluded_facilities: 0,
      covered_area_km2: 25.36,
      covered_pct: 34.7,
      coverage: null,
    },
  ],
}

function row(city: string) {
  return within(screen.getByRole('row', { name: new RegExp(city) }))
}

describe('StatisticsPanel', () => {
  it('counts schools and city-limit schools per city', () => {
    render(
      <StatisticsPanel
        cityNames={['Redlands', 'Yucaipa']}
        selectedCity={null}
        subtype={null}
        facilities={facilities}
        radius={null}
        proximity={idle()}
      />,
    )
    expect(row('Redlands').getAllByRole('cell').map((c) => c.textContent)).toEqual(['2', '1'])
    expect(row('Yucaipa').getAllByRole('cell').map((c) => c.textContent)).toEqual(['1', '1'])
    expect(screen.queryByText(/Area within/)).not.toBeInTheDocument()
    expect(screen.getByText(/straight-line distance/)).toBeInTheDocument()
  })

  it('shows coverage for the selected radius and city', () => {
    render(
      <StatisticsPanel
        cityNames={['Redlands', 'Yucaipa']}
        selectedCity="Redlands"
        subtype={null}
        facilities={facilities}
        radius={1000}
        proximity={idle({ data: proximity })}
      />,
    )
    expect(screen.getByRole('columnheader', { name: 'Area within 1 km' })).toBeInTheDocument()
    expect(row('Redlands').getByText('38.8%')).toBeInTheDocument()
    expect(row('Yucaipa').getByText('34.7%')).toBeInTheDocument()
    expect(
      screen.getByText(/36.38 of 93.86 km² lies within 1 km of 20 schools \(4 exclusively virtual excluded\)/),
    ).toBeInTheDocument()
    // Detail sentences only for the selected city
    expect(screen.queryByText(/25.36 of 73.13/)).not.toBeInTheDocument()
  })

  it('reports analysis errors with a retry button', async () => {
    const state = idle({ error: 'Database unavailable' })
    render(
      <StatisticsPanel
        cityNames={['Redlands', 'Yucaipa']}
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
