select *
from {{ ref('fct_mrr_daily') }}
where mrr_gbp < 0
   or paying_users < 0
