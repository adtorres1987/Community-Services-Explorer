import { describe, expect, it } from 'vitest'
import { makeFacility } from '../../test/fixtures'
import { gradeRange, isInFocus, matchesSubtype, schoolCategory, virtualLabel } from './schools'

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

describe('isInFocus', () => {
  const facility = makeFacility({ city: 'Yucaipa', facility_subtype: 'High' }).properties

  it('focuses study-area schools when no place is selected', () => {
    expect(isInFocus(facility, { city: null, subtype: null })).toBe(true)
  })

  it('applies place and subtype together', () => {
    expect(isInFocus(facility, { city: 'Yucaipa', subtype: 'High' })).toBe(true)
    expect(isInFocus(facility, { city: 'Redlands', subtype: 'High' })).toBe(false)
    expect(isInFocus(facility, { city: 'Yucaipa', subtype: 'Middle' })).toBe(false)
  })

  it('never focuses schools outside the study area', () => {
    const context = makeFacility({ city: null, in_study_area: false }).properties
    expect(isInFocus(context, { city: null, subtype: null })).toBe(false)
  })
})
