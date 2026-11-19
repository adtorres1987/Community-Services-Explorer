import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makeFacility, makeLibrary, makeStop } from '../test/fixtures'
import { FacilityPopup } from './FacilityPopup'

describe('FacilityPopup', () => {
  it('shows the main attributes', () => {
    render(<FacilityPopup facility={makeFacility().properties} />)
    expect(screen.getByRole('heading', { name: 'Test Elementary' })).toBeInTheDocument()
    expect(screen.getByText('Elementary · Grades KG–5')).toBeInTheDocument()
    expect(screen.getByText('1 Main St., Redlands, 92373')).toBeInTheDocument()
    expect(screen.getByText('Located in').nextSibling).toHaveTextContent('Redlands')
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

  it('notes when the mailing address names another city', () => {
    const facility = makeFacility({ city: 'Loma Linda', address_city: 'Redlands' })
    render(<FacilityPopup facility={facility.properties} />)
    expect(
      screen.getByText(/mailing address says Redlands, but the school is inside the Loma Linda boundary/),
    ).toBeInTheDocument()
  })

  it('explains schools outside the study area', () => {
    const facility = makeFacility({ city: null, address_city: 'Colton', in_study_area: false })
    render(<FacilityPopup facility={facility.properties} />)
    expect(screen.getByText('Outside the study area')).toBeInTheDocument()
    expect(screen.getByText(/count toward their proximity coverage/)).toBeInTheDocument()
    expect(screen.queryByText(/mailing address says/)).not.toBeInTheDocument()
  })

  it('does not link websites without an http(s) scheme', () => {
    const facility = makeFacility()
    facility.properties.attributes.Website = 'javascript:alert(1)'
    render(<FacilityPopup facility={facility.properties} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('shows library attributes', () => {
    render(<FacilityPopup facility={makeLibrary().properties} />)
    expect(screen.getByRole('heading', { name: 'A. K. Smiley Public Library' })).toBeInTheDocument()
    expect(screen.getByText('Central library')).toBeInTheDocument()
    expect(screen.getByText('System').nextSibling).toHaveTextContent('A. K. Smiley Public Library')
    expect(screen.getByText('125 W. Vine St., Redlands, 92373')).toBeInTheDocument()
    expect(screen.getByText('64,636 sq ft')).toBeInTheDocument()
    expect(screen.getByText('2,769 h/year (52 weeks)')).toBeInTheDocument()
    expect(screen.queryByText('District')).not.toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('explains libraries outside the study area', () => {
    const library = makeLibrary({ name: 'Calimesa Library', city: null, address_city: 'Calimesa', in_study_area: false })
    render(<FacilityPopup facility={library.properties} />)
    expect(screen.getByText(/not included in library counts/)).toBeInTheDocument()
  })

  it('shows transit service without an address note', () => {
    render(<FacilityPopup facility={makeStop().properties} />)
    expect(screen.getByText('Rail station · Rail')).toBeInTheDocument()
    expect(screen.getByText('Routes').nextSibling).toHaveTextContent('IE-OC Line, SB Line')
    expect(screen.getByText('86 departures')).toBeInTheDocument()
    expect(screen.getByText('5 per hour (7–9 am)')).toBeInTheDocument()
    expect(screen.getByText('No information')).toBeInTheDocument()
    // GTFS has no mailing address, so no address mismatch note
    expect(screen.queryByText(/mailing address/)).not.toBeInTheDocument()
  })

  it('explains a stop without weekday service', () => {
    const stop = makeStop({
      name: 'Main @ 1st',
      facility_subtype: 'No weekday service',
      proximity_eligible: false,
      attributes: { Agency: 'Omnitrans', Mode: 'Bus', Routes: '', WeekdayDepartures: 0, PeakDeparturesPerHour: 0 },
    })
    render(<FacilityPopup facility={stop.properties} />)
    expect(screen.getByText('Bus stop · No weekday service')).toBeInTheDocument()
    expect(screen.getByText(/stop is excluded from the proximity analysis/)).toBeInTheDocument()
  })
})
