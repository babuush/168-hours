# 168 Hours

7-day hourly weather forecasts for 5 Thai cities (Open-Meteo -> SQLite -> SQL).

## Setup

```
uv sync
uv run ingest.py    # fetch + load
uv run report.py    # write report.md and sql/results/
sqlite3 168hours.db
```

## Schema and grain

`city`: 5 static rows, seeded in `schema.sql`. `hourly_forecast`: PK
`(city_id, forecast_time_utc)`, one row per hour per city.

Grain: a row is the latest prediction for that hour, not a record of what
happened. Two runs disagree about the same future hour; the later run wins
via upsert. Full prediction history lives in the raw JSON on disk
(gitignored), not the DB.

## Idempotency

`ON CONFLICT (city_id, forecast_time_utc) DO UPDATE`. Verified live:

```
uv run ingest.py && uv run ingest.py && uv run ingest.py
sqlite3 168hours.db "SELECT count(*) FROM hourly_forecast;"   # 840
```

Caveat: 840 also holds for a broken pipeline that drops and re-adds one row
per hour as the 7-day window rolls forward, so the count alone is a weak
check. The real proof is re-running an hour apart and confirming an
overlapping key updates in place instead of duplicating:

```sql
SELECT count(*) FROM hourly_forecast
WHERE city_id = 1 AND forecast_time_utc = '<hour in both runs>';   -- 1
```

## Data issues

- `precip_prob_pct` can be null, every query orders `NULLS LAST`.
- Hourly array length comes back 167-169, not always 168, validated as
  160-176 rather than hardcoded.
- API is queried with `timezone=UTC`; local time (UTC+7) is derived in the
  transform. Every per-day query groups on `forecast_date_local`, never the
  UTC column, the easy way to get this quietly wrong.
- The first hourly bucket can already be in the past by the time the
  request lands.

## Running this hourly, all year

Not built, but the shape of it: append-only grain (keep every
`ingested_at_utc`, add a "latest" view) instead of upsert-in-place; monthly
partitioning once it's a year of history instead of a 7-day window; a
scheduler (n8n or Cloud Scheduler) to trigger the run; a freshness check
alerting if `max(ingested_at_utc)` goes stale; a retention policy on raw
JSON instead of keeping it forever.

## Insights

Hat Yai has the widest 7-day range despite being coastal (24-36°C, 12°C
spread), wider than inland Chiang Mai (7°C). Rain-chance peaks cluster in
the afternoon (14:00-19:00 local) across all 5 cities on nearly every day.

## AI usage

Built with Claude Code: the retry/backoff loop in `ingest.py`, the
window-function SQL (queries 3 and 4), and this README. I wrote the schema
and the transform/upsert logic, and reviewed every generated line before
committing it.

## What I left out, and why

No test file, no committed sample payload. The API is keyless and
re-running live is the actual idempotency proof, not a mock of it. No
orchestration, warehouse, or web app: 5 cities and 840 rows isn't a scale
problem, and a generated Markdown report is less friction to review than a
server.
