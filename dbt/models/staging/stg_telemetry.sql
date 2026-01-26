with src as (
    select *
    from read_parquet('{{ var("bronze_dir") }}/telemetry.parquet')
)

select
    asset_id,
    cast(ts as timestamp) as ts,
    lower(cast(status as varchar)) as status,
    cast(wind_speed_ms as double) as wind_speed_ms
from src
where asset_id is not null
  and ts is not null
