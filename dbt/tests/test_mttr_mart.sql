select *
from {{ ref('mart_mttr_region_daily') }}
where mttr_hours < 0
   or incident_count < 0
   or fleet_assets < 0
   or incidents_per_100_assets < 0