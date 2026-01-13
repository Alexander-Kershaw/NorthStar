select
    asset_id,
    ts,
    count(*) as n
from {{ ref('fct_asset_uptime_hourly') }}
group by 1, 2
having count(*) > 1
