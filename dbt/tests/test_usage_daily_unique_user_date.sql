select
    user_id,
    date_day,
    count(*) as n
from {{ ref('fct_usage_daily') }}
group by 1, 2
having count(*) > 1
