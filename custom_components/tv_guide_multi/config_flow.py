"""Config flow for the TV Guide Multi-Source integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow

from .const import DEFAULT_NAME, DOMAIN


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
