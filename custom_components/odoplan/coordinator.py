"""Fetches the numbers of every car of the account."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OdoPlanAuthError, OdoPlanClient, OdoPlanError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type OdoPlanConfigEntry = ConfigEntry[OdoPlanCoordinator]


class OdoPlanCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """The numbers of each car, by its slug."""

    config_entry: OdoPlanConfigEntry

    def __init__(self, hass: HomeAssistant, entry: OdoPlanConfigEntry, client: OdoPlanClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            cars = await self.client.cars()
            return {car["slug"]: await self.client.car(car["slug"]) for car in cars}
        except OdoPlanAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except OdoPlanError as err:
            raise UpdateFailed(str(err)) from err
