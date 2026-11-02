import type { FacilityProperties } from '../services/api'
import { gradeRange, virtualLabel } from '../features/facilities/schools'

interface Props {
  facility: FacilityProperties
}

export function FacilityPopup({ facility }: Props) {
  const { attributes } = facility
  const grades = gradeRange(facility)
  const address = [attributes.Street, facility.city, attributes.Zip].filter(Boolean).join(', ')
  const website =
    attributes.Website && /^https?:\/\//i.test(attributes.Website) ? attributes.Website : null

  return (
    <div className="facility-popup">
      <h3>{facility.name}</h3>
      <p className="facility-popup__subtitle">
        {facility.facility_subtype ?? 'School'}
        {grades && ` · Grades ${grades}`}
      </p>
      <dl>
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
      </dl>
      {!facility.proximity_eligible && (
        <p className="facility-popup__note">
          Exclusively virtual: this is an administrative address, so the school is excluded from
          the proximity analysis.
        </p>
      )}
      {!facility.in_city_limits && (
        <p className="facility-popup__note">
          The address says {facility.city}, but the location is outside the {facility.city} city
          limits.
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
