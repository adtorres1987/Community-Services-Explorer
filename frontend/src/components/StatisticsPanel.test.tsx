import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { ProximityResponse } from '../services/api'
import type { RequestState } from '../services/useRequest'
import { makeFacility, makePlace, makeResult } from '../test/fixtures'
import { StatisticsPanel } from './StatisticsPanel'

const places = [
  makePlace('Loma Linda', { population: 24939 }),
  makePlace('Mentone', { place_type: 'CDP', population: 9557 }),
  makePlace('Redlands', { population: 73161 }),
]

const facilities = [
  makeFacility({ id: 1, city: 'Redlands' }),
  makeFacility({ id: 2, city: 'Redlands' }),
  makeFacility({ id: 3, city: 'Mentone' }),
  makeFacility({ id: 4, city: 'Loma Linda' }),
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
    makeResult({
      city: 'Loma Linda',
      eligible_facilities: 1,
      excluded_facilities: 0,
      contributing_facility_ids: [4, 7, 8],
      city_area_km2: 23.2,
      covered_area_km2: 6.01,
      covered_pct: 25.9,
      population: 24939,
      covered_population: 7160,
      covered_population_pct: 28.7,
    }),
    makeResult({
      city: 'Mentone',
      eligible_facilities: 1,
      excluded_facilities: 0,
      contributing_facility_ids: [3, 9],
      city_area_km2: 15.85,
      covered_area_km2: 4.77,
      covered_pct: 30.1,
      population: 9557,
      covered_population: 6589,
      covered_population_pct: 68.9,
    }),
    makeResult({
      city: 'Redlands',
      eligible_facilities: 2,
      excluded_facilities: 4,
      // School 8 is in Loma Linda and also covers Redlands
      contributing_facility_ids: [1, 2, 8, 9],
      city_area_km2: 93.86,
      covered_area_km2: 37.17,
      covered_pct: 39.6,
      population: 73161,
      covered_population: 54741,
      covered_population_pct: 74.8,
    }),
  ],
}

function renderPanel(selectedCities: string[], radius: number | null, state = idle({ data: proximity })) {
  render(
    <StatisticsPanel
      places={places}
      selectedCities={selectedCities}
      subtype={null}
      facilities={facilities}
      radius={radius}
      proximity={state}
    />,
  )
  return state
}

function rowNames() {
  return screen.getAllByRole('row').slice(1).map((r) => within(r).getByRole('rowheader').textContent)
}

function detail() {
  return screen.getByText((_, element) => element?.classList.contains('stats-detail') ?? false)
    .textContent
}

function cells(name: RegExp) {
  return within(screen.getByRole('row', { name }))
    .getAllByRole('cell')
    .map((c) => c.textContent)
}

describe('StatisticsPanel', () => {
  it('shows every place and an "All" total when nothing is selected', () => {
    renderPanel([], null)
    expect(rowNames()).toEqual(['Loma Linda', 'MentoneCDP', 'Redlands', 'All (3)'])
    expect(cells(/^Redlands/)).toEqual(['2', '73,161'])
    expect(cells(/^All \(3\)/)).toEqual(['4', '107,657'])
    expect(screen.queryByText(/Residents within/)).not.toBeInTheDocument()
  })

  it('shows only the selected places and a weighted total for them', () => {
    renderPanel(['Mentone', 'Redlands'], 1000)
    expect(rowNames()).toEqual(['MentoneCDP', 'Redlands', 'Selected (2)'])
    expect(cells(/^Redlands/)).toEqual(['2', '74.8%', '39.6%'])
    // (6,589 + 54,741) / (9,557 + 73,161) and (4.77 + 37.17) / (15.85 + 93.86)
    expect(cells(/^Selected \(2\)/)).toEqual(['3', '74.1%', '38.2%'])
  })

  it('summarizes the selection in one sentence with distinct contributing schools', () => {
    renderPanel(['Mentone', 'Redlands'], 1000)
    // Contributing ids {3, 9} ∪ {1, 2, 8, 9} = 5 schools; 3 are inside the selection
    expect(detail()).toBe(
      '2 selected communities: 61,330 of 82,718 residents (74.1%) and 41.94 of 109.71 km² are ' +
        'within 1 km of a school. 5 schools contribute, including 2 outside the selection; ' +
        '4 exclusively virtual excluded.',
    )
  })

  it('names a single selected place and omits the total row', () => {
    renderPanel(['Loma Linda'], 1000)
    expect(rowNames()).toEqual(['Loma Linda'])
    expect(detail()).toMatch(/^Loma Linda: .* 3 schools contribute, including 2 outside Loma Linda\.$/)
  })

  it('labels the total "All" when every place is selected', () => {
    renderPanel(['Loma Linda', 'Mentone', 'Redlands'], 1000)
    expect(rowNames().at(-1)).toBe('All (3)')
    expect(detail()).toMatch(/^All communities: .*including \d+ outside the study area/)
  })

  it('reports analysis errors with a retry button', async () => {
    const state = renderPanel([], 500, idle({ error: 'Database unavailable' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Database unavailable')
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(state.retry).toHaveBeenCalledOnce()
  })
})
