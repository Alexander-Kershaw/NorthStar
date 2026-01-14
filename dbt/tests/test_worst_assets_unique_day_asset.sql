select
    date_day,
    asset_id,
    count(*) as n
from {{ ref('mart_worst_assets_daily') }}
group by 1, 2
having count(*) > 1
