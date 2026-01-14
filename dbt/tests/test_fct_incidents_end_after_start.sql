select *
from {{ ref('fct_incidents') }}
where end_ts <= start_ts
