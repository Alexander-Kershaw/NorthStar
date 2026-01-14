select
    asset_id,
    asset_type,
    region,
    installed_at,
    capacity_kw
from {{ ref('stg_assets') }}
