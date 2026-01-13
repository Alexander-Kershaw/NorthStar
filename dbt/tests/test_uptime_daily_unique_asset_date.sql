select
    asset_id,
    date_day,
    count(*) as n
from {{ ref('fct_asset_uptime_daily') }}
group by 1, 2
having count(*) > 1
