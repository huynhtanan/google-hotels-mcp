# Google Hotels MCP

> **New blog post:** [Add Google Hotels to Claude Desktop as an MCP server](https://dev.to/huynhtanan/add-google-hotels-to-claude-desktop-as-an-mcp-server-2-minute-setup-1m00) — 2-minute install walk-through for Claude Desktop and Claude Code.

[![Glama MCP server](https://glama.ai/mcp/servers/huynhtanan/google-hotels-mcp/badge)](https://glama.ai/mcp/servers/huynhtanan/google-hotels-mcp)

A Model Context Protocol (MCP) server that lets Claude, Cursor, Windsurf and any other MCP client fetch **live Google Hotels** and **Google Vacation Rentals** prices with the rate every booking site is charging (Booking.com, Expedia, Agoda, Vrbo, Airbnb, Hotels.com, …), plus a **3-month daily price calendar** for any single property. Everything comes back as JSON — no Google account, no scraping on your laptop, no Puppeteer.

Backed by three open-source actors on the Apify Store. You bring your own Apify token; the actors are pay-as-you-go on the Apify Free plan at **$0.002 / hotel**, **$0.0015 / daily price** and **$0.002 / vacation rental**. Apify ships $5 of free compute every month and no card is required to start.

## Tools

| Tool | What it does |
| ---- | ------------ |
| `search_hotels` | Google Hotels search for a destination + dates. Returns name, rating, review count, nightly and total price, hotel class, address, coordinates, amenities, hero photo, Google URL, and (optionally) the price every OTA is charging. |
| `hotel_price_calendar` | 3-month daily rate calendar for one hotel URL. One row per date with `price`, `currency`, `available`. |
| `search_vacation_rentals` | Google Vacation Rentals search (Airbnb / Vrbo / Booking.com). Same shape as hotels plus bedrooms/bathrooms. |

## Quick start

### 1. Get an Apify token
Create a free account at <https://console.apify.com/account/integrations> and copy your Personal API token. Pay-as-you-go, no card to start.

### 2. Add the server to your MCP client

> **Note:** this server is new and not yet on PyPI. Until it is, install directly from the GitHub repo with `uvx --from "git+https://github.com/huynhtanan/google-hotels-mcp.git@v0.1.2" google-hotels-mcp`. Pinned to the tagged release so later main-branch changes do not break existing users. Once google-hotels-mcp lands on PyPI you can drop the --from prefix.

**Claude Desktop** — edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "google-hotels": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/huynhtanan/google-hotels-mcp.git@v0.1.2", "google-hotels-mcp"],
      "env": { "APIFY_TOKEN": "apify_api_..." }
    }
  }
}
```

**Claude Code**:
```bash
claude mcp add google-hotels -- uvx --from "git+https://github.com/huynhtanan/google-hotels-mcp.git@v0.1.2" google-hotels-mcp --env APIFY_TOKEN=apify_api_...
```

**Cline** — in VS Code: open the Cline MCP Servers panel → Add server → Command, paste the same `uvx --from git+...` command and set `APIFY_TOKEN` in env.

**Cursor** — Settings → MCP → Add Server, same `uvx --from git+...` command with `APIFY_TOKEN` in env.

If you prefer `pipx` or `pip`, install from GitHub with `pipx install git+https://github.com/huynhtanan/google-hotels-mcp.git` (or `pip install git+...`) and run `google-hotels-mcp`.

## Example prompts

> *"Find hotels in Paris for 3 nights from 2026-12-20, two adults, in EUR, with the Booking.com and Expedia rate for each one."*

> *"Pull a 3-month daily price calendar for the Hoxton Paris — I want to see which dates are under €200."*

> *"Compare vacation rentals in Lisbon vs Porto, 2 adults, 2026-11-15 to 2026-11-22, 3+ bedrooms, with the Airbnb vs Vrbo rate for each."*

## Sample response

`search_hotels(query="hotels in Lisbon", check_in="2026-11-10", check_out="2026-11-13", adults=2, currency="EUR")` — one of 40 items (trimmed):

```json
{
  "name": "Patio São Vicente Guest Houses",
  "position": 1,
  "rating": 4.9,
  "reviewsCount": 349,
  "ratingDistribution": {"1": 0, "2": 0, "3": 3, "4": 16, "5": 330},
  "hotelClass": 4,
  "hotelClassText": "4-star hotel",
  "pricePerNight": 109,
  "pricePerNightText": "€109",
  "totalPrice": 372.1,
  "totalBeforeTaxes": 328.48,
  "currency": "EUR",
  "checkIn": "2026-11-10",
  "checkOut": "2026-11-13",
  "nights": 3,
  "checkInTime": "3:00 PM",
  "checkOutTime": "11:00 AM",
  "latitude": 38.7155846,
  "longitude": -9.1280593,
  "nearbyPlaces": [
    {"name": "National Pantheon", "travelTime": "6 min"},
    {"name": "Voz Operário", "travelTime": "2 min"}
  ],
  "reviewTopics": [
    {"topic": "Location", "mentions": 88, "positive": 84, "negative": 2, "positiveShare": 0.977}
  ],
  "amenityIds": [29, 2, 54, 15, 12, 1, 11, 25],
  "website": "https://www.patiosaovicente.com/",
  "mapsUrl": "https://www.google.com/maps?cid=1945275941691630548",
  "googleHotelsUrl": "https://www.google.com/travel/hotels/entity/ChkIn4CU6sjxgJ1YGg0vZy8xMWY0XzdqenhqEAE?hl=en&gl=us"
}
```

Set `include_provider_prices=true` and the hotel also gets a `providers` array with the price Booking.com, Expedia, Agoda, Hotels.com, Vrbo and 10+ other OTAs are each charging for the same stay.

## Pricing

| Call | Cost |
| ---- | ---- |
| 1 hotel in `search_hotels` | $0.002 |
| 1 hotel with per-provider rates | $0.004 ($0.002 result + $0.002 provider enrich) |
| 1 date in `hotel_price_calendar` | $0.0015 |
| 1 vacation rental in `search_vacation_rentals` | $0.002 |

A full-city hotel search (20 hotels with provider rates) is around **$0.08**. The Apify Free plan ships $5 of credit every month — about 60 full-city searches — before you need to upgrade.

## How it compares

| | google-hotels-mcp | HasData google-hotels-mcp | Scraping yourself |
| :-- | :-- | :-- | :-- |
| Open source | ✅ MIT | ❌ | depends |
| MCP tools | 3 (hotels, calendar, rentals) | 1 (hotels) | 0 |
| Daily price calendar | ✅ | ❌ | hard |
| Vacation rentals | ✅ Airbnb + Vrbo + Booking.com | ❌ | hard |
| Per-provider rates | ✅ 15+ OTAs | ✅ | hard |
| Pricing | $0.002 / hotel pay-as-you-go | 10 credits / search | your time |
| Free tier | $5 / month Apify credit | 1,000 credits / month | n/a |

## FAQ

**Do I need an Apify paid plan?** No. The free plan is enough for a few thousand hotel results per month.

**Is this official from Google?** No, it is an unofficial server that calls the same `/travel/hotels` endpoints a browser does, via three open actors.

**Why three actors instead of one?** Google serves calendars and vacation rentals on separate pages, each with its own ranking signals. Keeping them as separate tools keeps costs honest — you only pay for what the agent actually fetches.

**What about rate limits?** Each actor retries transient failures and respects Google's rate limits. For heavy workloads use the Apify Scheduler (one line in the console) instead of running the MCP tool in a tight loop.

## Links

- GitHub: <https://github.com/huynhtanan/google-hotels-mcp>
- Hotels actor: <https://apify.com/zet46/google-hotels-scraper>
- Price-calendar actor: <https://apify.com/zet46/google-hotels-price-calendar>
- Vacation-rentals actor: <https://apify.com/zet46/google-vacation-rentals-scraper>
- Python client with examples: <https://github.com/huynhtanan/google-hotels-api>

## License

MIT.

<!-- mcp-name: io.github.huynhtanan/google-hotels-mcp -->

## Examples

Runnable, self-contained scripts that use this MCP server (and the underlying Apify actors) for real workflows.

- [`examples/rate_parity`](examples/rate_parity) — Daily OTA rate-parity watcher: snapshots per-OTA prices into SQLite and prints hotels where Booking/Expedia/Agoda disagree by ≥ 3% on the same stay date.
- [`examples/cheapest_week`](examples/cheapest_week) — Find the cheapest 7-night window for one hotel in the next 60 days by pulling the Google Hotels price calendar and sorting every rolling window by total price.

## Tutorials

Deep-dive write-up on dev.to:

- [Add Google Hotels to Claude Desktop as an MCP server (2-minute setup)](https://dev.to/huynhtanan/add-google-hotels-to-claude-desktop-as-an-mcp-server-2-minute-setup-1m00)

Full series (all four actors): [Apify + Python: scrapers, trackers, and Claude Desktop](https://dev.to/huynhtanan/series/45271).
