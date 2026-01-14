***
# Semantic Layer (MetricFlow)
***

NorthStar defines a dbt Semantic Layer with a daily time spine and three initial KPIs:
- `mrr_gbp`
- `dau`
- `uptime_pct`

## List metrics
```bash
mf list metrics
```

***

## Some Example Queries:

MRR by month:

```bash
mf query --metrics mrr_gbp --group-by metric_time__month
```

DAU by day:

```bash
mf query --metrics dau --group-by metric_time
```

Uptime by week:

```bash
mf query --metrics uptime_pct --group-by metric_time__week
```

***
