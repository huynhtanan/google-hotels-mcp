"""Google Hotels MCP server.

Exposes three tools backed by Apify actors on the Apify Store:
- search_hotels: live Google Hotels results for a destination + dates
- hotel_price_calendar: 3-month daily rate calendar for one property
- search_vacation_rentals: Google Vacation Rentals (Airbnb/Vrbo) results

Users bring their own APIFY_TOKEN. Pay per run on the Apify Store at
$0.002/hotel, $0.0015/daily-price, $0.002/vacation-rental.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

APIFY_BASE = "https://api.apify.com/v2"
HOTELS_ACTOR = "zet46~google-hotels-scraper"
CALENDAR_ACTOR = "zet46~google-hotels-price-calendar"
RENTALS_ACTOR = "zet46~google-vacation-rentals-scraper"

mcp = FastMCP("google-hotels")


def _token() -> str:
    tok = os.environ.get("APIFY_TOKEN")
    if not tok:
        raise RuntimeError(
            "APIFY_TOKEN environment variable is not set. "
            "Create a free token at https://console.apify.com/account/integrations"
        )
    return tok


def _run_sync(actor: str, body: dict[str, Any], timeout_s: int = 300) -> list[dict[str, Any]]:
    url = f"{APIFY_BASE}/acts/{actor}/run-sync-get-dataset-items"
    headers = {"Authorization": f"Bearer {_token()}"}
    with httpx.Client(timeout=httpx.Timeout(timeout_s)) as client:
        r = client.post(url, headers=headers, json=body)
    if r.status_code >= 400:
        raise RuntimeError(f"Apify {actor} failed: HTTP {r.status_code} {r.text[:400]}")
    return r.json()


@mcp.tool()
def search_hotels(
    query: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    children: int = 0,
    rooms: int = 1,
    currency: str = "USD",
    hl: str = "en",
    gl: str = "us",
    max_results: int = 20,
    min_rating: float | None = None,
    min_hotel_class: int | None = None,
    include_provider_prices: bool = False,
) -> str:
    """Search Google Hotels for a destination between two dates.

    Returns a JSON array of hotels with name, rating, review count, price per
    night, total price, hotel class, address, coordinates, amenities, hero
    photo and the Google /travel/hotels/entity URL. When ``include_provider_prices``
    is true each hotel also gets a ``providers`` list with the rate every booking
    site (Booking.com, Expedia, Agoda, Vrbo, Hotels.com, ...) is charging for
    the stay (one extra Apify provider-prices call per hotel, billed per-hotel).

    Args:
        query: destination, e.g. ``"hotels in Paris"`` or ``"Hilton near Louvre"``.
        check_in: ISO date ``YYYY-MM-DD``.
        check_out: ISO date ``YYYY-MM-DD``.
        adults: number of adults.
        children: number of children.
        rooms: number of rooms.
        currency: ISO 4217 code (``USD``, ``EUR``, ``GBP``, ...).
        hl: Google interface language (``en``, ``fr``, ``de``, ...).
        gl: Google country code (``us``, ``gb``, ``fr``, ...).
        max_results: upper bound on hotels returned.
        min_rating: filter to hotels at or above this guest rating (0-5).
        min_hotel_class: filter to hotels at or above this class (2-5).
        include_provider_prices: fetch per-provider rates. Each hotel priced
            this way adds one ``provider-prices`` call to the Apify bill.
            Defaults to ``false`` to keep costs predictable.
    """
    body: dict[str, Any] = {
        "queries": [query],
        "checkIn": check_in,
        "checkOut": check_out,
        "adults": adults,
        "children": children,
        "rooms": rooms,
        "currency": currency,
        "language": hl,
        "country": gl,
        "maxHotelsPerQuery": max_results,
        "includeProviderPrices": include_provider_prices,
    }
    if min_rating is not None:
        body["minRating"] = min_rating
    if min_hotel_class is not None:
        body["minHotelClass"] = min_hotel_class
    items = _run_sync(HOTELS_ACTOR, body)
    return json.dumps(items, ensure_ascii=False)


@mcp.tool()
def hotel_price_calendar(
    hotel_url: str,
    start_date: str,
    number_of_dates: int = 90,
    nights: int = 1,
    currency: str = "USD",
    hl: str = "en",
    gl: str = "us",
    adults: int = 2,
    children: int = 0,
    rooms: int = 1,
) -> str:
    """Return a daily rate calendar for one Google Hotels property.

    By default this returns 90 forward dates (roughly three months), one row
    per date. Each item has ``date``, ``price``, ``currency`` and ``available``.

    Args:
        hotel_url: a Google ``/travel/hotels/entity/<token>`` URL.
        start_date: ISO date ``YYYY-MM-DD`` where the calendar starts.
        number_of_dates: how many forward dates to price (default 90 = 3 months).
        nights: stay length to price per date (1 = per-night rate).
        currency: ISO 4217 code.
        hl: Google interface language.
        gl: Google country code.
        adults: number of adults for the stay.
        children: number of children.
        rooms: number of rooms.
    """
    body = {
        "hotels": [hotel_url],
        "startDate": start_date,
        "numberOfDates": number_of_dates,
        "nights": nights,
        "currency": currency,
        "language": hl,
        "country": gl,
        "adults": adults,
        "children": children,
        "rooms": rooms,
    }
    items = _run_sync(CALENDAR_ACTOR, body)
    return json.dumps(items, ensure_ascii=False)


@mcp.tool()
def search_vacation_rentals(
    query: str,
    check_in: str,
    check_out: str,
    adults: int = 2,
    children: int = 0,
    currency: str = "USD",
    hl: str = "en",
    gl: str = "us",
    max_results: int = 20,
    include_provider_prices: bool = False,
) -> str:
    """Search Google Vacation Rentals (Airbnb / Vrbo / Booking.com) for a stay.

    Returns a JSON array of rentals with title, nightly price, total price,
    rating, review count, bedrooms, bathrooms, amenities, hero photo and the
    Google /travel/vacation-rentals/entity URL. When
    ``include_provider_prices`` is true each rental also gets a ``providers``
    list with the price every listing site (Airbnb, Vrbo, Booking.com) is
    charging (one extra provider-prices call per rental, billed per-rental).

    Args:
        query: destination, e.g. ``"vacation rentals in Lisbon"``.
        check_in: ISO date ``YYYY-MM-DD``.
        check_out: ISO date ``YYYY-MM-DD``.
        adults: number of adults.
        children: number of children.
        currency: ISO 4217 code.
        hl: Google interface language.
        gl: Google country code.
        max_results: upper bound on rentals returned.
        include_provider_prices: fetch per-provider rates. Each rental priced
            this way adds one ``provider-prices`` call to the Apify bill.
            Defaults to ``false`` to keep costs predictable.
    """
    body = {
        "queries": [query],
        "checkIn": check_in,
        "checkOut": check_out,
        "adults": adults,
        "children": children,
        "currency": currency,
        "language": hl,
        "country": gl,
        "maxHotelsPerQuery": max_results,
        "includeProviderPrices": include_provider_prices,
    }
    items = _run_sync(RENTALS_ACTOR, body)
    return json.dumps(items, ensure_ascii=False)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
