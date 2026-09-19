"""Refreshes TV schedules on a fixed interval, with stale-data fallback."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Optional, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .sources import Schedule, ScheduleSource

_LOGGER = logging.getLogger(__name__)

# "Ora in onda" needs to actually change during the day; a plain per-calendar-day
# cache never refreshes again after the first poll. sorrisi.com does not publish
# a change-frequency guarantee, so 10 minutes is a compromise between freshness
# and not hammering their servers.
REFRESH_INTERVAL = timedelta(minutes=10)


def _merge_with_previous(current: Schedule, previous: Optional[Schedule]) -> Schedule:
    """Fall back to the previous successful parse when the new one is empty.

    An empty parse almost always means the source changed its markup (a
    schedule with genuinely nothing on air is not a real scenario). Keeping
    the last known-good schedule instead of collapsing straight to "Nessun
    dato" buys time to notice and fix the parser before the sensors go blank.
    """
    return current if current else (previous or current)


class SorrisiCoordinator(DataUpdateCoordinator[Tuple[Schedule, Schedule]]):
    """Refreshes both schedules together on a fixed interval.

    A single coordinator shared by both sensors, instead of a per-sensor cache,
    is also what keeps this to one fetch per source per refresh rather than two.
    """

    def __init__(self, hass: HomeAssistant, source: ScheduleSource) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="TV Guide Multi-Source",
            update_interval=REFRESH_INTERVAL,
        )
        self._source = source

    async def _async_update_data(self) -> Tuple[Schedule, Schedule]:
        previous = self.data
        now, prime = await self._source.get_schedules()
        if previous is not None:
            prev_now, prev_prime = previous
            now = _merge_with_previous(now, prev_now)
            prime = _merge_with_previous(prime, prev_prime)
        return now, prime
