select
    user_id,
    created_at,
    country,
    signup_channel
from {{ ref('stg_users') }}

