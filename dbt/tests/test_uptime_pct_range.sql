select *
from {{ ref('fct_asset_uptime_daily') }}
where uptime_pct < 0
   or uptime_pct > 1
