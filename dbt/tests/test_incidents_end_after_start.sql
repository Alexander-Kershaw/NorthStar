-- Fails if any incident has an end time that is not after its start time
select *
from {{ ref('stg_incidents') }}
where end_ts <= start_ts