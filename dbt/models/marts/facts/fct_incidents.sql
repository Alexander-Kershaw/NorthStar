select
    incident_id,
    asset_id,
    start_ts,
    end_ts,
    duration_hours,
    severity,
    cause
from {{ ref('stg_incidents') }}
