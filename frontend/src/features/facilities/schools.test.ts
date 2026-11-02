import { describe, expect, it } from 'vitest'
import { makeFacility } from '../../test/fixtures'
import { gradeRange, matchesFilters, schoolCategory, virtualLabel } from './schools'

describe('schoolCategory', () => {
  it('keeps the main school types', () => {
    expect(schoolCategory('Elementary')).toBe('Elementary')
    expect(schoolCategory('K-12')).toBe('K-12')
  })

  it('groups other types and missing values as Other', () => {
    expect(schoolCategory('Continuation')).toBe('Other')
    expect(schoolCategory('Community Day')).toBe('Other')
    expect(schoolCategory(null)).toBe('Other')
  })
})

describe('gradeRange', () => {
  it('drops leading zeros and joins with an en dash', () => {
    expect(gradeRange(makeFacility().properties)).toBe('KG–5')
  })

  it('shows a single grade once', () => {
    const facility = makeFacility()
    facility.properties.attributes.GradeLow = '12'
    facility.properties.attributes.GradeHigh = '12'
    expect(gradeRange(facility.properties)).toBe('12')
  })

  it('returns null when a bound is missing', () => {
    const facility = makeFacility()
    facility.properties.attributes.GradeHigh = null
    expect(gradeRange(facility.properties)).toBeNull()
  })
})

describe('virtualLabel', () => {
  it('maps CDE codes and falls back to Unknown', () => {
    expect(virtualLabel('V')).toBe('Exclusively virtual')
    expect(virtualLabel('C')).toBe('Primarily in person')
    expect(virtualLabel('X')).toBe('Unknown')
    expect(virtualLabel(null)).toBe('Unknown')
  })
})

describe('matchesFilters', () => {
  const facility = makeFacility({ city: 'Yucaipa', facility_subtype: 'High' }).properties

  it('matches when filters are empty', () => {
    expect(matchesFilters(facility, { city: null, subtype: null })).toBe(true)
  })

  it('applies city and subtype together', () => {
    expect(matchesFilters(facility, { city: 'Yucaipa', subtype: 'High' })).toBe(true)
    expect(matchesFilters(facility, { city: 'Redlands', subtype: 'High' })).toBe(false)
    expect(matchesFilters(facility, { city: 'Yucaipa', subtype: 'Middle' })).toBe(false)
  })
})
