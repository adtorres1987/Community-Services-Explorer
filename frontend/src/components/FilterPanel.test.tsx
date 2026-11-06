import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { makePlace } from '../test/fixtures'
import { FilterPanel } from './FilterPanel'

const places = [makePlace('Colton'), makePlace('Mentone', { place_type: 'CDP' }), makePlace('Rialto')]

function renderPanel(cities: string[]) {
  const onCitiesChange = vi.fn()
  render(
    <FilterPanel
      places={places}
      subtypes={['Elementary', 'High']}
      cities={cities}
      subtype={null}
      radius={null}
      onCitiesChange={onCitiesChange}
      onSubtypeChange={vi.fn()}
      onRadiusChange={vi.fn()}
    />,
  )
  return onCitiesChange
}

describe('FilterPanel communities', () => {
  it('lists every community as a checkbox', () => {
    renderPanel([])
    const group = screen.getByRole('group', { name: 'Communities' })
    expect(group).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox').map((c) => (c as HTMLInputElement).checked)).toEqual([
      false,
      false,
      false,
    ])
    expect(screen.getByText('Showing all communities.')).toBeInTheDocument()
  })

  it('adds a community and keeps the list order', async () => {
    const onCitiesChange = renderPanel(['Rialto'])
    await userEvent.click(screen.getByRole('checkbox', { name: 'Colton' }))
    expect(onCitiesChange).toHaveBeenCalledWith(['Colton', 'Rialto'])
  })

  it('removes a community', async () => {
    const onCitiesChange = renderPanel(['Colton', 'Rialto'])
    expect(screen.getByText('2 of 3 selected.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('checkbox', { name: 'Colton' }))
    expect(onCitiesChange).toHaveBeenCalledWith(['Rialto'])
  })

  it('selects all or none', async () => {
    const onCitiesChange = renderPanel(['Colton'])
    await userEvent.click(screen.getByRole('button', { name: 'All' }))
    expect(onCitiesChange).toHaveBeenLastCalledWith(['Colton', 'Mentone', 'Rialto'])
    await userEvent.click(screen.getByRole('button', { name: 'None' }))
    expect(onCitiesChange).toHaveBeenLastCalledWith([])
  })

  it('disables "None" when nothing is selected', () => {
    renderPanel([])
    expect(screen.getByRole('button', { name: 'None' })).toBeDisabled()
  })
})
