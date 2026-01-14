select *
from {{ ref('mart_uptime_region_daily') }}
where avg_uptime_pct < 0
   or avg_uptime_pct > 1