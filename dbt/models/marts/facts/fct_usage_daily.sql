with events as (
    select
        user_id,
        cast(event_ts as date) as date_day,
        event_type
    from {{ ref('stg_events') }}
),
agg as (
    select
        user_id,
        date_day,
        count(*) as event_count,
        sum(case when event_type = 'create_alert' then 1 else 0 end) as create_alert_count,
        sum(case when event_type = 'export_report' then 1 else 0 end) as export_report_count
    from events
    group by 1, 2
)

select
    user_id,
    date_day,
    event_count,
    create_alert_count,
    export_report_count,
    case when event_count > 0 then 1 else 0 end as is_active
from agg
