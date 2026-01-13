with src as (
    select *
    from read_parquet('../data/bronze/assets.parquet')
)

select
    asset_id,
    lower(cast(asset_type as varchar)) as asset_type,
    lower(cast(region as varchar)) as region,
    cast(installed_at as date) as installed_at,
    cast(capacity_kw as integer) as capacity_kw
from src
where asset_id is not null


