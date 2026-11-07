"""Constants for the OdoPlan integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "odoplan"

DEFAULT_URL: Final = "https://www.odoplan.ch"

# OdoPlan's numbers change with a new reading, at most a few times a day.
SCAN_INTERVAL: Final = timedelta(minutes=15)

SERVICE_ADD_READING: Final = "add_reading"
ATTR_DEVICE_ID: Final = "device_id"
ATTR_KM: Final = "km"
ATTR_DATE: Final = "date"
