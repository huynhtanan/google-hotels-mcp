# examples/rate_parity

A tiny rate-parity watcher that uses this MCP server to pull per-OTA prices
for a list of hotels, stores each snapshot in SQLite, and prints any
drift ≥ 3% between the cheapest and reference booking site for the same
hotel on the same stay date.

Companion to the dev.to post *Build a hotel rate-parity watcher with Claude
Desktop and SQLite*.

## Install

```bash
cd examples/rate_parity
pip install httpx
export APIFY_TOKEN=apify_api_...
```

The script talks to the Apify REST API directly (no MCP client needed) so
you can also run it as a cron / scheduled task. If you prefer Claude
Desktop, see the "Driving it from Claude" section at the bottom.

## One-shot run

Snapshot 20 Paris hotels for the next 7 nights, EUR, two adults:

```bash
python rate_parity.py \
    --query "hotels in Paris" \
    --check-in 2026-11-15 \
    --nights 7 \
    --currency EUR
```

This writes `rate_parity.db` next to the script and prints any rate-parity
drift rows at the end.

## Later: just the report

```bash
python rate_parity.py --report
```

Re-reads the latest `captured_at` per `(hotel, stay_date, ota)` and prints
drift rows against the current snapshot without hitting Apify.

## Schema

```sql
CREATE TABLE snapshot (
  captured_at TEXT NOT NULL,  -- ISO UTC timestamp of the fetch
  hotel       TEXT NOT NULL,
  stay_date   TEXT NOT NULL,  -- YYYY-MM-DD
  ota         TEXT NOT NULL,  -- "Booking.com", "Expedia", "Agoda", ...
  price       REAL NOT NULL,
  currency    TEXT NOT NULL,
  PRIMARY KEY (captured_at, hotel, stay_date, ota)
);
```

## Cost

- 20 hotels × 1 night = 20 provider-prices calls
- `search_hotels` with `includeProviderPrices=true`: `$0.002/hotel + $0.002/provider-prices` row
- Daily cost at 20 hotels × 7 forward nights ≈ **$0.56/day** (≈ $17/mo)

Apify's free tier is $5 of credit per month — about 9 days of this pattern
before you need the $49/mo plan. If you only monitor one hotel across 30
forward nights (`$0.12/day`), you stay in the free tier year-round.

## Driving it from Claude Desktop

If this MCP server is wired into Claude Desktop (see repo root `README.md`),
you can skip the CLI entirely:

> "Snapshot 20 Paris hotels for the next 30 nights with
> `include_provider_prices=true`, EUR, two adults, and append each row to
> `rate_parity.db` using the schema above."

Claude calls `search_hotels` once per date, parses the `providers` field,
and inserts rows. Then ask:

> "Report tonight's rate-parity drift rows that are ≥ 3% deep. Pick the top
> three by estimated 10-night revenue loss."

The whole scrape → diff → prioritize → explain loop stays inside a single
Claude Desktop session.
