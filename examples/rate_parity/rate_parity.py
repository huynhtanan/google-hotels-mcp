"""Rate-parity watcher backed by the Google Hotels MCP server.

Takes a hotel list and a date range, pulls per-OTA prices through the
``search_hotels`` tool (with ``include_provider_prices=True``), stores
each snapshot in SQLite, and prints any drift >=3% between the cheapest
and the reference OTA for the same hotel + same stay date.

Usage (standalone, without an MCP client):

    export APIFY_TOKEN=apify_api_...
    python rate_parity.py --query "hotels in Paris" --check-in 2026-11-15 \
        --nights 7 --currency EUR

If you call it from Claude Desktop (recommended), ask Claude:

    "Snapshot 20 Paris hotels for the next 30 nights with
    include_provider_prices=true, EUR, two adults, and insert each row into
    rate_parity.db following the schema in rate_parity.py."

Then run ``python rate_parity.py --report`` to print today's drift rows.

The threshold (3%) is a sensible default for rate-parity audits; adjust
``DRIFT_PCT`` for your tolerance.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
from typing import Any

import httpx

APIFY_BASE = "https://api.apify.com/v2"
HOTELS_ACTOR = "zet46~google-hotels-scraper"
DB_PATH = os.environ.get("RATE_PARITY_DB", "rate_parity.db")
DRIFT_PCT = -3.0  # drift at least this deep triggers an alert


SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot (
  captured_at TEXT NOT NULL,
  hotel       TEXT NOT NULL,
  stay_date   TEXT NOT NULL,
  ota         TEXT NOT NULL,
  price       REAL NOT NULL,
  currency    TEXT NOT NULL,
  PRIMARY KEY (captured_at, hotel, stay_date, ota)
);
CREATE INDEX IF NOT EXISTS snapshot_recent
  ON snapshot (hotel, stay_date, captured_at DESC);
"""


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    return db


def _token() -> str:
    tok = os.environ.get("APIFY_TOKEN")
    if not tok:
        print("APIFY_TOKEN not set. Create a free token at "
              "https://console.apify.com/account/integrations", file=sys.stderr)
        sys.exit(2)
    return tok


def snapshot(query: str, check_in: str, nights: int, currency: str,
             adults: int = 2, max_results: int = 20) -> int:
    """Pull one night per date in the range and store per-OTA rows.

    Returns the number of (hotel, date, ota) rows inserted.
    """
    db = connect()
    captured_at = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    inserted = 0
    base = dt.date.fromisoformat(check_in)
    headers = {"Authorization": f"Bearer {_token()}"}
    url = f"{APIFY_BASE}/acts/{HOTELS_ACTOR}/run-sync-get-dataset-items"

    for offset in range(nights):
        ci = base + dt.timedelta(days=offset)
        co = ci + dt.timedelta(days=1)
        body = {
            "queries": [query],
            "checkIn": ci.isoformat(),
            "checkOut": co.isoformat(),
            "adults": adults,
            "currency": currency,
            "maxResults": max_results,
            "includeProviderPrices": True,
        }
        print(f"[fetch] {ci} -> {co} …", file=sys.stderr)
        with httpx.Client(timeout=httpx.Timeout(300)) as c:
            r = c.post(url, headers=headers, json=body)
        r.raise_for_status()
        for hotel in r.json():
            name = hotel.get("name")
            if not name:
                continue
            for p in hotel.get("providers") or hotel.get("providerPrices") or []:
                price = p.get("price") or p.get("rate")
                ota = p.get("name") or p.get("provider")
                if price is None or ota is None:
                    continue
                db.execute(
                    "INSERT OR REPLACE INTO snapshot "
                    "(captured_at, hotel, stay_date, ota, price, currency) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (captured_at, name, ci.isoformat(), ota, float(price), currency),
                )
                inserted += 1
        db.commit()
    print(f"[ok] inserted {inserted} rows at {captured_at}", file=sys.stderr)
    return inserted


REPORT_SQL = """
WITH latest AS (
  SELECT hotel, stay_date, ota, price, currency,
         ROW_NUMBER() OVER (
           PARTITION BY hotel, stay_date, ota
           ORDER BY captured_at DESC
         ) AS rn
  FROM snapshot
),
today AS (SELECT * FROM latest WHERE rn = 1),
agg AS (
  SELECT hotel, stay_date, currency,
         MIN(price) AS cheapest, MAX(price) AS reference,
         COUNT(DISTINCT ota) AS ota_count
  FROM today GROUP BY hotel, stay_date, currency
  HAVING ota_count >= 2
)
SELECT hotel, stay_date, currency, cheapest, reference,
       ROUND((cheapest - reference) * 100.0 / reference, 2) AS delta_pct
FROM agg
WHERE (cheapest - reference) * 100.0 / reference <= ?
ORDER BY delta_pct ASC
LIMIT 50;
"""


def report() -> None:
    db = connect()
    rows = db.execute(REPORT_SQL, (DRIFT_PCT,)).fetchall()
    if not rows:
        print("No rate-parity drift >= "
              f"{abs(DRIFT_PCT):.1f}% in the latest snapshot.")
        return
    print(f"{'hotel':40s}  {'date':12s}  {'cur':3s}  {'cheapest':>9s}  "
          f"{'reference':>9s}  {'delta':>7s}")
    for hotel, date, cur, cheapest, reference, delta in rows:
        print(f"{hotel[:40]:40s}  {date:12s}  {cur:3s}  {cheapest:9.2f}  "
              f"{reference:9.2f}  {delta:6.2f}%")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--query", help="e.g. 'hotels in Paris'")
    p.add_argument("--check-in", help="YYYY-MM-DD")
    p.add_argument("--nights", type=int, default=7)
    p.add_argument("--currency", default="EUR")
    p.add_argument("--adults", type=int, default=2)
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--report", action="store_true",
                   help="print today's drift rows (no fetch)")
    args = p.parse_args()
    if args.report:
        report()
        return
    if not (args.query and args.check_in):
        p.error("--query and --check-in are required when --report is not set")
    snapshot(args.query, args.check_in, args.nights, args.currency,
             args.adults, args.max_results)
    report()


if __name__ == "__main__":
    main()
