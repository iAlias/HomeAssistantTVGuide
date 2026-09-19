"""Config flow for the TV Guide Multi-Source integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

from .const import CONF_FAVORITES, DEFAULT_NAME, DOMAIN


class TvGuideMultiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TV Guide Multi-Source."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Single-step setup: the integration polls one public source, so a
        single instance is enough."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        schema = vol.Schema({vol.Optional("name", default=DEFAULT_NAME): str})
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "TvGuideMultiOptionsFlow":
        return TvGuideMultiOptionsFlow(config_entry)


class TvGuideMultiOptionsFlow(OptionsFlow):
    """Lets the user configure favorite programs after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        # Explicit assignment (rather than relying on the base class) keeps
        # this working on HA versions older than the 2024.11 auto-injection,
        # matching the 2024.1.0 minimum declared in hacs.json.
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(CONF_FAVORITES, "")
        schema = vol.Schema({vol.Optional(CONF_FAVORITES, default=current): str})
        return self.async_show_form(step_id="init", data_schema=schema)
