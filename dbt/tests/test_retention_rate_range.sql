select *
from {{ ref('mart_retention_cohorts') }}
where retained_d7_rate < 0
   or retained_d7_rate > 1
   or retained_d30_rate < 0
   or retained_d30_rate > 1
