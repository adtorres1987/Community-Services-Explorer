import type { FacilityProperties } from '../services/api'
import { gradeRange, virtualLabel } from '../features/facilities/schools'
import { floorArea, openingHours } from '../features/facilities/libraries'

interface Props {
  facility: FacilityProperties
}

function SchoolDetails({ facility }: Props) {
  const { attributes } = facility
  const address = [attributes.Street, facility.address_city, attributes.Zip].filter(Boolean).join(', ')
  return (
    <>
      <dt>District</dt>
      <dd>{attributes.DistrictName ?? '—'}</dd>
      <dt>Address</dt>
      <dd>{address || '—'}</dd>
      <dt>Enrollment</dt>
      <dd>{attributes.EnrollTotal?.toLocaleString('en-US') ?? '—'}</dd>
      <dt>Charter</dt>
      <dd>{attributes.Charter === 'Y' ? 'Yes' : 'No'}</dd>
      <dt>Instruction</dt>
      <dd>{virtualLabel(attributes.Virtual)}</dd>
    </>
  )
}

function LibraryDetails({ facility }: Props) {
  const { attributes } = facility
  const address = [attributes.Address, facility.address_city, attributes.Zip].filter(Boolean).join(', ')
  return (
    <>
      <dt>System</dt>
      <dd>{attributes.LibrarySystem ?? '—'}</dd>
      <dt>Address</dt>
      <dd>{address || '—'}</dd>
      <dt>Size</dt>
      <dd>{floorArea(facility) ?? '—'}</dd>
      <dt>Open</dt>
      <dd>{openingHours(facility) ?? '—'}</dd>
    </>
  )
}

export function FacilityPopup({ facility }: Props) {
  const isSchool = facility.facility_type === 'school'
  const noun = isSchool ? 'school' : 'library'
  const grades = isSchool ? gradeRange(facility) : null
  const website =
    facility.attributes.Website && /^https?:\/\//i.test(facility.attributes.Website)
      ? facility.attributes.Website
      : null

  return (
    <div className="facility-popup">
      <h3>{facility.name}</h3>
      <p className="facility-popup__subtitle">
        {isSchool ? (facility.facility_subtype ?? 'School') : `${facility.facility_subtype ?? 'Public'} library`}
        {grades && ` · Grades ${grades}`}
      </p>
      <dl>
        <dt>Located in</dt>
        <dd>{facility.city ?? 'Outside the study area'}</dd>
        {isSchool ? <SchoolDetails facility={facility} /> : <LibraryDetails facility={facility} />}
      </dl>
      {!facility.in_study_area && (
        <p className="facility-popup__note">
          Outside the study communities. Shown because it is close enough to count toward
          their proximity coverage; not included in {noun} counts.
        </p>
      )}
      {facility.in_study_area && facility.address_city !== facility.city && (
        <p className="facility-popup__note">
          The mailing address says {facility.address_city}, but the {noun} is inside the{' '}
          {facility.city} boundary.
        </p>
      )}
      {!facility.proximity_eligible && (
        <p className="facility-popup__note">
          Exclusively virtual: this is an administrative address, so the school is excluded from
          the proximity analysis.
        </p>
      )}
      {website && (
        <a href={website} target="_blank" rel="noreferrer">
          School website
        </a>
      )}
    </div>
  )
}
