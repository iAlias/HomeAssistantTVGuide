"""Tests for the stale-data fallback in SorrisiCoordinator.

If sorrisi.com changes its markup, ``_parse_programs`` starts returning empty
mappings. Rather than let the sensors immediately show "Nessun dato", the
coordinator keeps serving the last successfully parsed schedule.
"""

import asyncio

from custom_components.tv_guide_multi.coordinator import SorrisiCoordinator, _merge_with_previous
from custom_components.tv_guide_multi.sources import ScheduleSource
from homeassistant.core import HomeAssistant


def test_merge_with_previous_keeps_current_when_non_empty():
    current = {"Rai 1": {"titolo": "TG1"}}
    previous = {"Rai 1": {"titolo": "Vecchio programma"}}
    assert _merge_with_previous(current, previous) == current


def test_merge_with_previous_falls_back_when_current_empty():
    previous = {"Rai 1": {"titolo": "Vecchio programma"}}
    assert _merge_with_previous({}, previous) == previous


def test_merge_with_previous_returns_empty_when_nothing_to_fall_back_to():
    assert _merge_with_previous({}, None) == {}
    assert _merge_with_previous({}, {}) == {}


class _FakeSource(ScheduleSource):
    """Returns a scripted sequence of (now, prime) results, one per call."""

    def __init__(self, results):
        self._results = list(results)

    async def get_schedules(self):
        return self._results.pop(0)


def test_coordinator_falls_back_to_last_good_schedule_on_empty_refresh():
    good_now = {"Rai 1": {"titolo": "TG1"}}
    good_prime = {"Rai 1": {"titolo": "Film"}}
    source = _FakeSource([
        (good_now, good_prime),
        ({}, {}),  # simulates sorrisi.com's markup breaking
    ])
    coordinator = SorrisiCoordinator(HomeAssistant(), source)

    asyncio.run(coordinator.async_refresh())
    assert coordinator.data == (good_now, good_prime)

    asyncio.run(coordinator.async_refresh())
    assert coordinator.data == (good_now, good_prime)


def test_coordinator_adopts_new_data_once_source_recovers():
    good_now = {"Rai 1": {"titolo": "TG1"}}
    good_prime = {"Rai 1": {"titolo": "Film"}}
    new_now = {"Rai 1": {"titolo": "Nuovo programma"}}
    source = _FakeSource([
        (good_now, good_prime),
        ({}, {}),
        (new_now, good_prime),
    ])
    coordinator = SorrisiCoordinator(HomeAssistant(), source)

    asyncio.run(coordinator.async_refresh())
    asyncio.run(coordinator.async_refresh())
    asyncio.run(coordinator.async_refresh())

    assert coordinator.data == (new_now, good_prime)
