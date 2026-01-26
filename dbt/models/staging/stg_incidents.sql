with src as (
    select *
    from read_parquet('{{ var("bronze_dir") }}/incidents.parquet')
)

select
    incident_id,
    asset_id,
    cast(start_ts as timestamp) as start_ts,
    cast(end_ts as timestamp) as end_ts,
    cast(duration_hours as integer) as duration_hours,
    lower(cast(severity as varchar)) as severity,
    lower(cast(cause as varchar)) as cause
from src
where incident_id is not null
  and asset_id is not null
  and start_ts is not null
  and end_ts is not null
