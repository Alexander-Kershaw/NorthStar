select *
from {{ ref('mart_revenue_summary_monthly') }}
where avg_mrr_gbp < 0
   or end_of_month_mrr_gbp < 0
   or avg_paying_users < 0
   or end_of_month_paying_users < 0
