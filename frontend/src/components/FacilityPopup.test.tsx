import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeFacility } from '../test/fixtures'
import { FacilityPopup } from './FacilityPopup'

describe('FacilityPopup', () => {
  it('shows the main attributes', () => {
    render(<FacilityPopup facility={makeFacility().properties} />)
    expect(screen.getByRole('heading', { name: 'Test Elementary' })).toBeInTheDocument()
    expect(screen.getByText('Elementary · Grades KG–5')).toBeInTheDocument()
    expect(screen.getByText('1 Main St., Redlands, 92373')).toBeInTheDocument()
    expect(screen.getByText('512')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'School website' })).toHaveAttribute(
      'href',
      'https://example.org',
    )
    expect(screen.queryByText(/excluded from/)).not.toBeInTheDocument()
  })

  it('explains why a virtual school is excluded from proximity', () => {
    const facility = makeFacility({ proximity_eligible: false })
    facility.properties.attributes.Virtual = 'V'
    render(<FacilityPopup facility={facility.properties} />)
    expect(screen.getByText(/excluded from the proximity analysis/)).toBeInTheDocument()
  })

  it('notes a school outside its city limits', () => {
    render(<FacilityPopup facility={makeFacility({ in_city_limits: false }).properties} />)
    expect(screen.getByText(/outside the Redlands city limits/)).toBeInTheDocument()
  })

  it('does not link websites without an http(s) scheme', () => {
    const facility = makeFacility()
    facility.properties.attributes.Website = 'javascript:alert(1)'
    render(<FacilityPopup facility={facility.properties} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
