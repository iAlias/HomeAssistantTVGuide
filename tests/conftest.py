"""Make ``coordinator.py`` importable without a Home Assistant installation.

``coordinator.py`` imports ``homeassistant.core`` and
``homeassistant.helpers.update_coordinator`` purely for typing/base-class
purposes; none of that machinery is exercised by the pure-logic tests here
(``_parse_programs`` and friends). Rather than pull in the full
``homeassistant`` package as a test dependency, this installs minimal stand-in
modules in ``sys.modules`` before the first import, mirroring the approach
used in the ``allerte-italia`` project's ``conftest.py``.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "tv_guide_multi"
sys.path.insert(0, str(COMPONENT_DIR))


class _GenericStub:
    """Base class that tolerates ``Stub[SomeType]`` subscription syntax."""

    def __class_getitem__(cls, item):
        return cls


def _install_stub_homeassistant() -> None:
    if "homeassistant" in sys.modules:
        return

    modules = {name: types.ModuleType(name) for name in (
        "homeassistant",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.update_coordinator",
    )}

    class HomeAssistant:
        pass

    class DataUpdateCoordinator(_GenericStub):
        def __init__(self, hass, logger, *, name=None, update_interval=None):
            self.data = None

        async def async_refresh(self):
            self.data = await self._async_update_data()

        async def async_config_entry_first_refresh(self):
            self.data = await self._async_update_data()

    modules["homeassistant.core"].HomeAssistant = HomeAssistant
    modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = DataUpdateCoordinator

    sys.modules.update(modules)


_install_stub_homeassistant()
