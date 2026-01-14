with t as (
    select
        asset_id,
        ts,
        case when status = 'up' then 1 else 0 end as is_up
    from {{ ref('stg_telemetry') }}
)

select
    asset_id,
    ts,
    is_up
from t
