with src as (
    select *
    from read_parquet('../data/bronze/events.parquet')
),
cleaned as (
    select
        event_id,
        user_id,
        nullif(trim(lower(cast(event_type as varchar))), '') as event_type,
        cast(event_ts as timestamp) as event_ts
    from src
)
select
    event_id,
    user_id,
    case
        when event_type in ('none', 'nan', 'null') then null
        else event_type
    end as event_type,
    event_ts
from cleaned
where event_id is not null
  and event_type is not null
  and event_type not in ('none', 'nan', 'null')
