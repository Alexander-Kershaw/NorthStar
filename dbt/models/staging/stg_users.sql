with src as (
    select *
    from read_parquet('{{ var("bronze_dir") }}/users.parquet')
)

select
    user_id,
    cast(created_at as timestamp) as created_at,
    upper(country) as country,
    lower(signup_channel) as signup_channel
from src
