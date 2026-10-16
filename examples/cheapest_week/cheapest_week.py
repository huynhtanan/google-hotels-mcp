"""Find the cheapest 7-night window for one hotel in the next 60 days.

Companion to the Google Hotels MCP server. Pulls a 60-day forward price
calendar through the ``hotel_price_calendar`` actor (or, by name, through
the ``hotel_price_calendar`` MCP tool), then sorts every possible
7-consecutive-night window by total price and prints the five cheapest.

Usage (standalone, without an MCP client):

    export APIFY_TOKEN=apify_api_...
    python cheapest_week.py --hotel "Ritz Paris" --nights 7 \
        --horizon 60 --currency EUR

Or from Claude Desktop:

    "Call hotel_price_calendar for 'Ritz Paris' starting today for 60
    forward dates in EUR. Then sort every rolling 7-night window by
    total price and show me the five cheapest check-in dates."

The horizon is capped at 60 to keep each actor call inside its 512 MB
memory budget. Longer horizons may OOM.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Any

import httpx

APIFY_BASE = "https://api.apify.com/v2"
CALENDAR_ACTOR = "zet46~google-hotels-price-calendar"
DEFAULT_HORIZON = 60
DEFAULT_NIGHTS = 7
DEFAULT_MEMORY_MB = 512


def _token() -> str:
    tok = os.environ.get("APIFY_TOKEN")
    if not tok:
        print(
            "APIFY_TOKEN not set. Create a free token at "
            "https://console.apify.com/account/integrations",
            file=sys.stderr,
        )
        sys.exit(2)
    return tok


def fetch_calendar(
    hotel: str,
    start_date: str,
    horizon: int,
    currency: str,
    language: str,
    country: str,
    adults: int,
    memory_mb: int = DEFAULT_MEMORY_MB,
) -> list[dict[str, Any]]:
    token = _token()
    body = {
        "hotels": [hotel],
        "startDate": start_date,
        "numberOfDates": horizon,
        "nights": 1,
        "currency": currency,
        "language": language,
        "country": country,
        "adults": adults,
    }
    with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
        r = client.post(
            f"{APIFY_BASE}/acts/{CALENDAR_ACTOR}/runs",
            params={"token": token, "memory": memory_mb},
            json=body,
        )
        r.raise_for_status()
        run_id = r.json()["data"]["id"]
        for _ in range(60):
            time.sleep(5)
            s = client.get(
                f"{APIFY_BASE}/actor-runs/{run_id}",
                params={"token": token},
            )
            status = s.json()["data"]["status"]
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
        else:
            raise RuntimeError(f"run {run_id} did not finish in 5 minutes")
        if status != "SUCCEEDED":
            raise RuntimeError(f"run {run_id} ended as {status}")
        ds = s.json()["data"]["defaultDatasetId"]
        items = client.get(
            f"{APIFY_BASE}/datasets/{ds}/items",
            params={"token": token},
        ).json()
    return [i for i in items if isinstance(i, dict)]


def cheapest_windows(
    calendar: list[dict[str, Any]],
    nights: int,
) -> list[dict[str, Any]]:
    rows = sorted(calendar, key=lambda i: i["checkIn"])
    windows: list[dict[str, Any]] = []
    for i in range(len(rows) - nights + 1):
        window = rows[i : i + nights]
        if not all(w.get("available") for w in window):
            continue
        prices = [w.get("lowestTotalPrice") for w in window]
        if not all(isinstance(p, (int, float)) for p in prices):
            continue
        total = round(sum(prices), 2)
        windows.append(
            {
                "check_in": window[0]["checkIn"],
                "check_out": window[-1]["checkIn"],
                "nights": nights,
                "currency": window[0].get("currency"),
                "total": total,
                "avg_per_night": round(total / nights, 2),
            }
        )
    windows.sort(key=lambda w: w["total"])
    return windows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hotel", required=True, help="e.g. 'Ritz Paris'")
    ap.add_argument(
        "--start",
        default=dt.date.today().isoformat(),
        help="first check-in date, ISO (default: today)",
    )
    ap.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
    ap.add_argument("--nights", type=int, default=DEFAULT_NIGHTS)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--language", default="en")
    ap.add_argument("--country", default="us")
    ap.add_argument("--adults", type=int, default=2)
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()

    calendar = fetch_calendar(
        args.hotel,
        args.start,
        args.horizon,
        args.currency,
        args.language,
        args.country,
        args.adults,
    )
    print(
        f"{len(calendar)} dates priced for {args.hotel} "
        f"({args.start} .. +{args.horizon}d, {args.currency})"
    )
    windows = cheapest_windows(calendar, args.nights)
    if not windows:
        print("no fully-available window found")
        return 1
    print(f"\ntop {args.top} cheapest {args.nights}-night windows:")
    for w in windows[: args.top]:
        print(
            f"  {w['currency']} {w['total']:>9} "
            f"({w['avg_per_night']}/night) "
            f"check-in {w['check_in']} .. {w['check_out']}"
        )
    print(f"\nmost expensive:")
    for w in windows[-1:]:
        print(
            f"  {w['currency']} {w['total']:>9} "
            f"({w['avg_per_night']}/night) "
            f"check-in {w['check_in']} .. {w['check_out']}"
        )
    cheapest = windows[0]["total"]
    peak = windows[-1]["total"]
    delta_pct = (peak - cheapest) * 100.0 / peak
    print(f"\ngap: {delta_pct:.1f}% ({cheapest} vs {peak})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
