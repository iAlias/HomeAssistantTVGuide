"""Fetches and parses Italian TV schedules from ``sorrisi.com``."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Dict, Tuple

import aiohttp
import async_timeout
from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# "Ora in onda" needs to actually change during the day; a plain per-calendar-day
# cache never refreshes again after the first poll. Sorrisi.com does not publish
# a change-frequency guarantee, so 10 minutes is a compromise between freshness
# and not hammering their servers.
REFRESH_INTERVAL = timedelta(minutes=10)

URL_NOW = "https://www.sorrisi.com/guidatv/ora-in-tv/"
URL_PRIME = "https://www.sorrisi.com/guidatv/stasera-in-tv/"

CHANNEL_ORDER = [
    "Rai 1",
    "Rai 2",
    "Rai 3",
    "Rete 4",
    "Canale 5",
    "Italia 1",
    "La7",
    "TV8",
    "NOVE",
]

SKIP_CHANNELS = {
    "IRIS",
    "CANALE20",
    "20",
    "20MEDIASET",
    "RAI4",
}


# -----------------------------------------------------------------------------
# fetching utilities
# -----------------------------------------------------------------------------

async def _fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with async_timeout.timeout(15):
            resp = await session.get(url)
            if resp.status != 200:
                _LOGGER.warning("Sorrisi: %s status %s", url, resp.status)
                return ""
            return await resp.text()
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Error fetching %s: %s", url, err)
        return ""


def _parse_programs(html: str) -> Dict[str, str]:
    """Return a mapping {channel: title} from the provided HTML."""
    soup = BeautifulSoup(html, "html.parser")
    mapping: Dict[str, str] = {}

    for header in soup.select("div.gtv-channel-header"):
        logo = header.find("a", class_="gtv-logo")
        channel = logo.get("data-channel-name") if logo else header.get_text(strip=True)

        article = header.find_next("article", class_="gtv-program-on-air") or \
            header.find_next("article", class_="gtv-program")
        title_el = article.find("h3", class_="gtv-program-title") if article else None
        if channel and title_el:
            key = channel.upper().replace(" ", "")
            if key in SKIP_CHANNELS:
                continue
            mapping[channel.strip()] = title_el.get_text(strip=True)

    def sort_key(item: Tuple[str, str]) -> Tuple[int, str]:
        try:
            idx = CHANNEL_ORDER.index(item[0])
        except ValueError:
            idx = len(CHANNEL_ORDER)
        return idx, item[0]

    return dict(sorted(mapping.items(), key=sort_key))


async def get_schedules(session: aiohttp.ClientSession) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Download and parse schedules from ``sorrisi.com``."""
    html_now, html_prime = await asyncio.gather(
        _fetch_page(session, URL_NOW),
        _fetch_page(session, URL_PRIME),
    )
    return _parse_programs(html_now), _parse_programs(html_prime)


# -----------------------------------------------------------------------------
# Coordinator
# -----------------------------------------------------------------------------

class SorrisiCoordinator(DataUpdateCoordinator[Tuple[Dict[str, str], Dict[str, str]]]):
    """Refreshes both schedules together on a fixed interval.

    A single coordinator shared by both sensors, instead of a per-sensor cache,
    is also what keeps this to 2 downloads per refresh rather than 4.
    """

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="TV Guide Multi-Source",
            update_interval=REFRESH_INTERVAL,
        )
        self._session = session

    async def _async_update_data(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        return await get_schedules(self._session)
