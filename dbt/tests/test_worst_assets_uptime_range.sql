select *
from {{ ref('mart_worst_assets_daily') }}
where uptime_pct < 0
   or uptime_pct > 1
