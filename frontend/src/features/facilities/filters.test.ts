import { describe, expect, it } from 'vitest'
import { makeFacility } from '../../test/fixtures'
import { isInFocus, isSelected, matchesSubtype } from './filters'

describe('matchesSubtype', () => {
  const facility = makeFacility({ facility_subtype: 'High' }).properties

  it('matches any type when no subtype is selected', () => {
    expect(matchesSubtype(facility, null)).toBe(true)
  })

  it('matches only the selected subtype', () => {
    expect(matchesSubtype(facility, 'High')).toBe(true)
    expect(matchesSubtype(facility, 'Middle')).toBe(false)
  })
})

describe('isSelected', () => {
  it('treats an empty selection as all places', () => {
    expect(isSelected('Colton', [])).toBe(true)
  })

  it('matches only selected places', () => {
    expect(isSelected('Colton', ['Colton', 'Rialto'])).toBe(true)
    expect(isSelected('Redlands', ['Colton', 'Rialto'])).toBe(false)
  })

  it('never selects facilities outside the study area', () => {
    expect(isSelected(null, ['Colton'])).toBe(false)
  })
})

describe('isInFocus', () => {
  const facility = makeFacility({ city: 'Yucaipa', facility_subtype: 'High' }).properties

  it('focuses study-area schools when no place is selected', () => {
    expect(isInFocus(facility, { cities: [], subtype: null })).toBe(true)
  })

  it('focuses schools in any of the selected places', () => {
    expect(isInFocus(facility, { cities: ['Redlands', 'Yucaipa'], subtype: null })).toBe(true)
    expect(isInFocus(facility, { cities: ['Redlands', 'Colton'], subtype: null })).toBe(false)
  })

  it('applies places and subtype together', () => {
    expect(isInFocus(facility, { cities: ['Yucaipa'], subtype: 'High' })).toBe(true)
    expect(isInFocus(facility, { cities: ['Yucaipa'], subtype: 'Middle' })).toBe(false)
  })

  it('never focuses schools outside the study area', () => {
    const context = makeFacility({ city: null, in_study_area: false }).properties
    expect(isInFocus(context, { cities: [], subtype: null })).toBe(false)
  })
})
