"""Make ``sensor.py`` importable without a Home Assistant installation.

``sensor.py`` imports several ``homeassistant.*`` modules at the top level
purely for typing/base-class purposes (``SensorEntity``, ``DataUpdateCoordinator``,
...); none of that machinery is exercised by the pure-logic tests here
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
        "homeassistant.components",
        "homeassistant.components.sensor",
        "homeassistant.const",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.aiohttp_client",
        "homeassistant.helpers.config_validation",
        "homeassistant.helpers.update_coordinator",
    )}

    class SensorEntity:
        pass

    class HomeAssistant:
        pass

    class DataUpdateCoordinator(_GenericStub):
        def __init__(self, hass, logger, *, name=None, update_interval=None):
            self.data = None

        async def async_refresh(self):
            self.data = await self._async_update_data()

    class CoordinatorEntity(_GenericStub):
        def __init__(self, coordinator):
            self.coordinator = coordinator

    class _PlatformSchema:
        def extend(self, *_args, **_kwargs):
            return self

    def async_get_clientsession(hass):
        raise NotImplementedError("stubbed for tests; not used by pure-logic tests")

    modules["homeassistant.components.sensor"].SensorEntity = SensorEntity
    modules["homeassistant.const"].CONF_NAME = "name"
    modules["homeassistant.core"].HomeAssistant = HomeAssistant
    modules["homeassistant.helpers.aiohttp_client"].async_get_clientsession = async_get_clientsession
    modules["homeassistant.helpers.config_validation"].PLATFORM_SCHEMA = _PlatformSchema()
    modules["homeassistant.helpers.config_validation"].string = str
    modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = DataUpdateCoordinator
    modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = CoordinatorEntity

    sys.modules.update(modules)


_install_stub_homeassistant()
