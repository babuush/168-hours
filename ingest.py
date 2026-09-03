import logging
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

DB_PATH = "168hours.db"
LOCAL_OFFSET = timedelta(hours=7)


def fetch_forecast(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation,precipitation_probability",
        "forecast_days": 7,
        "timezone": "UTC",
    }
    for attempt in range(4):
        try:
            response = requests.get(url, params=params, timeout=(5, 20))
        except requests.exceptions.Timeout:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
            continue

        if response.status_code >= 500:
            if attempt == 3:
                response.raise_for_status()
            time.sleep(2 ** attempt)
            continue

        response.raise_for_status()
        return response.json()


def transform(data):
    hourly = data["hourly"]
    times = hourly["time"]
    temps = hourly["temperature_2m"]
    precip = hourly["precipitation"]
    precip_prob = hourly["precipitation_probability"]

    n = len(times)
    if not (len(temps) == len(precip) == len(precip_prob) == n):
        raise ValueError("hourly arrays have mismatched lengths")
    if not (160 <= n <= 176):
        raise ValueError(f"unexpected hourly array length: {n}")

    ingested_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for i in range(n):
        utc_dt = datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc)
        local_dt = utc_dt + LOCAL_OFFSET
        rows.append((
            times[i],
            local_dt.date().isoformat(),
            local_dt.hour,
            temps[i],
            precip[i],
            precip_prob[i],
            ingested_at,
        ))
    return rows


def upsert_rows(conn, city_id, rows):
    conn.execute("BEGIN")
    try:
        for forecast_time_utc, date_local, hour_local, temp, precip, precip_prob, ingested_at in rows:
            conn.execute(
                """
                INSERT INTO hourly_forecast (
                    city_id, forecast_time_utc, forecast_date_local, forecast_hour_local,
                    temperature_c, precipitation_mm, precip_prob_pct, ingested_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (city_id, forecast_time_utc) DO UPDATE SET
                    forecast_date_local = excluded.forecast_date_local,
                    forecast_hour_local = excluded.forecast_hour_local,
                    temperature_c = excluded.temperature_c,
                    precipitation_mm = excluded.precipitation_mm,
                    precip_prob_pct = excluded.precip_prob_pct,
                    ingested_at_utc = excluded.ingested_at_utc
                """,
                (city_id, forecast_time_utc, date_local, hour_local, temp, precip, precip_prob, ingested_at),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    conn = sqlite3.connect(DB_PATH)
    cities = conn.execute("SELECT city_id, slug, latitude, longitude FROM city").fetchall()

    any_failed = False
    for city_id, slug, latitude, longitude in cities:
        try:
            data = fetch_forecast(latitude, longitude)
            rows = transform(data)
            upsert_rows(conn, city_id, rows)
            logging.info(f"{slug}: ingested {len(rows)} rows")
        except Exception as e:
            logging.error(f"{slug}: failed - {e}")
            any_failed = True

    conn.close()
    if any_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
