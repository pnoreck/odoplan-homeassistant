"""Setting up OdoPlan with the personal key from a car's "Automation" page."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import OdoPlanAuthError, OdoPlanClient, OdoPlanError
from .const import DEFAULT_URL, DOMAIN

KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class OdoPlanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Asks for OdoPlan's address and the key, and tries them."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """The address, OdoPlan's own by default, and the key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            self._async_abort_entries_match({CONF_URL: url, CONF_API_KEY: user_input[CONF_API_KEY]})
            errors, cars = await self._try(url, user_input[CONF_API_KEY])
            if not errors:
                return self.async_create_entry(
                    title=_title(cars), data={CONF_URL: url, CONF_API_KEY: user_input[CONF_API_KEY]}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Required(CONF_URL): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)), vol.Required(CONF_API_KEY): KEY_SELECTOR}),
                user_input or {CONF_URL: DEFAULT_URL},
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """The key was renewed or deleted in OdoPlan."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Asks for the new key."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors, _ = await self._try(entry.data[CONF_URL], user_input[CONF_API_KEY])
            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_API_KEY: user_input[CONF_API_KEY]})

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): KEY_SELECTOR}),
            errors=errors,
        )

    async def _try(self, url: str, api_key: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
        try:
            cars = await OdoPlanClient(async_get_clientsession(self.hass), url, api_key).cars()
        except OdoPlanAuthError:
            return {"base": "invalid_auth"}, []
        except OdoPlanError:
            return {"base": "cannot_connect"}, []
        return {}, cars


def _title(cars: list[dict[str, Any]]) -> str:
    names = [car["name"] for car in cars]
    return "OdoPlan" + (f" ({', '.join(names)})" if names else "")
