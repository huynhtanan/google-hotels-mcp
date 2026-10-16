# examples/cheapest_week

Point this script at one hotel and it tells you the cheapest 7-night (or
however long) window to book in the next two months, sorted by total
nightly price. Backed by the `hotel_price_calendar` tool from this MCP
server, so you get the same per-date rates Google Hotels shows.

Companion to the dev.to post *Find the cheapest week to book a hotel in
the next two months with Claude Desktop*.

## Install

```bash
cd examples/cheapest_week
pip install httpx
export APIFY_TOKEN=apify_api_...
```

The script talks to the Apify REST API directly (no MCP client needed),
so it also runs from cron / Task Scheduler if you want a nightly digest.
If you prefer Claude Desktop, see the "Driving it from Claude" section.

## One-shot run

```bash
python cheapest_week.py --hotel "Ritz Paris" --nights 7 \
    --horizon 60 --currency EUR
```

Sample output (Ritz Paris, EUR, 60-day horizon, Nov 2026 start):

```
60 dates priced for Ritz Paris (2026-11-15 .. +60d, EUR)

top 5 cheapest 7-night windows:
  EUR   15454.5 (2207.79/night) check-in 2026-11-15 .. 2026-11-21
  EUR  15636.25 (2233.75/night) check-in 2026-11-16 .. 2026-11-22
  EUR  15682.66 (2240.38/night) check-in 2027-01-03 .. 2027-01-09
  EUR  15682.66 (2240.38/night) check-in 2027-01-04 .. 2027-01-10
  EUR 15999.869 (2285.70/night) check-in 2026-11-17 .. 2026-11-23

most expensive:
  EUR  21010.61 (3001.52/night) check-in 2026-12-17 .. 2026-12-23

gap: 26.4% (15454.5 vs 21010.61)
```

The spread between the cheapest week (mid-November) and the Christmas
week is **26.4%** — €5,556 on a 7-night stay for the same room.

## Driving it from Claude Desktop

Once the MCP server is installed (see the main [README](../../README.md)),
ask Claude:

> *"Call `hotel_price_calendar` for 'Ritz Paris' starting today for 60
> forward dates in EUR, two adults. Sort every rolling 7-night window by
> total price and show me the five cheapest check-in dates alongside the
> most expensive week in the window."*

Claude handles the sort entirely from the returned data — no second
actor call needed.

## Why 60 and not 90

The actor serves up to roughly 90 forward dates from Google's calendar,
but at 90 dates a single 256 MB container occasionally OOMs because the
intermediate protobuf grows past the budget. The script asks for 512 MB
and caps the horizon at 60 to stay comfortably inside that envelope.
Raise `--horizon` only if you also raise `memory_mb` in the script.

## Cost

- One call × 60 dates = **$0.09** per hotel at the current
  `$0.0015/date` price (actor
  [zet46/google-hotels-price-calendar](https://apify.com/zet46/google-hotels-price-calendar))
- Apify's $5 free monthly credit covers about **55 one-hotel runs** —
  enough to re-check every day for close to two months without touching
  the paid plan
- Scanning your whole competitive set (e.g. 20 city hotels) once a week:
  20 × $0.09 = **$1.80/week** on the free tier for 2.5 weeks, then $49/mo

Pay-per-result — you only pay for the dates that priced. Dates Google
cannot serve (far-future, sold-out) do not count.
