"""OdoPlan: your kilometre allowance for lease and insurance in Home Assistant."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import OdoPlanClient, OdoPlanError
from .const import ATTR_DATE, ATTR_DEVICE_ID, ATTR_KM, DOMAIN, SERVICE_ADD_READING
from .coordinator import OdoPlanConfigEntry, OdoPlanCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

ADD_READING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_KM): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional(ATTR_DATE): cv.date,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Registers the action that enters a reading."""

    async def add_reading(call: ServiceCall) -> ServiceResponse:
        device = dr.async_get(hass).async_get(call.data[ATTR_DEVICE_ID])
        slug = next((identifier for domain, identifier in device.identifiers if domain == DOMAIN), None) if device else None
        entry: OdoPlanConfigEntry | None = next(
            (entry for entry in hass.config_entries.async_loaded_entries(DOMAIN) if device is not None and _belongs(device, entry)),
            None,
        )
        if slug is None or entry is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_car")

        try:
            result = await entry.runtime_data.client.add_reading(slug, call.data[ATTR_KM], call.data.get(ATTR_DATE))
        except OdoPlanError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="reading_refused", translation_placeholders={"message": str(err)}
            ) from err
        await entry.runtime_data.async_request_refresh()
        return result

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_READING, add_reading, schema=ADD_READING_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: OdoPlanConfigEntry) -> bool:
    """Connects to OdoPlan with the key and loads the cars."""
    client = OdoPlanClient(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_KEY])
    coordinator = OdoPlanCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OdoPlanConfigEntry) -> bool:
    """Removes the cars' sensors."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _belongs(device: dr.DeviceEntry, entry: OdoPlanConfigEntry) -> bool:
    """Whether the car's device comes from this entry; config_entry_id since Home Assistant 2026."""
    entry_id = getattr(device, "config_entry_id", None)
    return entry_id == entry.entry_id if entry_id is not None else entry.entry_id in device.config_entries
