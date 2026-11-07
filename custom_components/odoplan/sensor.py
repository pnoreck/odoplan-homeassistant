"""A car's numbers from OdoPlan as sensors, one device per car."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OdoPlanConfigEntry, OdoPlanCoordinator

PARALLEL_UPDATES = 0

KM_PER_DAY = "km/d"
LITERS_PER_100_KM = "L/100km"
CHF = "CHF"

type Car = dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class OdoPlanSensorDescription(SensorEntityDescription):
    """A number of OdoPlan's answer, and whether a car has it at all."""

    value_fn: Callable[[Car], Any]
    exists_fn: Callable[[Car], bool] = lambda car: True


def _get(car: Car, *path: str) -> Any:
    value: Any = car
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _distance(key: str, value_fn: Callable[[Car], Any], **kwargs: Any) -> OdoPlanSensorDescription:
    return OdoPlanSensorDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=kwargs.pop("state_class", SensorStateClass.MEASUREMENT),
        suggested_display_precision=0,
        value_fn=value_fn,
        **kwargs,
    )


def _has_contract(car: Car) -> bool:
    return car.get("contract") is not None


SENSORS: tuple[OdoPlanSensorDescription, ...] = (
    _distance("buffer", lambda car: car.get("buffer_km")),
    OdoPlanSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=["good", "warning", "critical"],
        value_fn=lambda car: car.get("status"),
    ),
    _distance("week_left", lambda car: car.get("week_left_km")),
    _distance("month_left", lambda car: car.get("month_left_km")),
    _distance("next_month", lambda car: car.get("next_month_km")),
    _distance(
        "odometer",
        lambda car: _get(car, "last_reading", "km"),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    OdoPlanSensorDescription(
        key="last_reading",
        translation_key="last_reading",
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda car: _date(_get(car, "last_reading", "date")),
    ),
    _distance("driven", lambda car: car.get("driven_km"), state_class=SensorStateClass.TOTAL_INCREASING),
    _distance("allowed", lambda car: car.get("allowed_km"), entity_registry_enabled_default=False),
    OdoPlanSensorDescription(
        key="pace",
        translation_key="pace",
        native_unit_of_measurement=KM_PER_DAY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda car: car.get("pace_per_day_km"),
    ),
    OdoPlanSensorDescription(
        key="everyday",
        translation_key="everyday",
        native_unit_of_measurement=KM_PER_DAY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=lambda car: car.get("everyday_per_day_km"),
    ),
    _distance("contract_left", lambda car: _get(car, "contract", "left_km"), exists_fn=_has_contract),
    _distance("contract_projected", lambda car: _get(car, "contract", "projected_km"), exists_fn=_has_contract),
    OdoPlanSensorDescription(
        key="contract_end",
        translation_key="contract_end",
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda car: _date(_get(car, "contract", "end")),
        exists_fn=_has_contract,
    ),
    _distance("year_projected", lambda car: _get(car, "year", "projected_km")),
    _distance("excess", lambda car: _get(car, "excess", "km")),
    OdoPlanSensorDescription(
        key="excess_cost",
        translation_key="excess_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CHF,
        suggested_display_precision=0,
        value_fn=lambda car: _get(car, "excess", "cost"),
    ),
    _distance("next_contract", lambda car: car.get("next_contract_km")),
    OdoPlanSensorDescription(
        key="electric_share",
        translation_key="electric_share",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda car: _get(car, "energy", "electric_share_percent"),
        exists_fn=lambda car: car.get("powertrain") == "plug_in_hybrid",
    ),
    OdoPlanSensorDescription(
        key="fuel_consumption",
        translation_key="fuel_consumption",
        native_unit_of_measurement=LITERS_PER_100_KM,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda car: _get(car, "energy", "fuel_l_per_100_km"),
        exists_fn=lambda car: car.get("powertrain") != "electric",
    ),
    OdoPlanSensorDescription(
        key="energy_cost",
        translation_key="energy_cost",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CHF,
        suggested_display_precision=2,
        value_fn=lambda car: _get(car, "energy", "cost_per_100_km"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: OdoPlanConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Adds each car's sensors, and those of cars added in OdoPlan later."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def add_new_cars() -> None:
        new = [slug for slug in coordinator.data if slug not in known]
        known.update(new)
        async_add_entities(
            OdoPlanSensor(coordinator, slug, description)
            for slug in new
            for description in SENSORS
            if description.exists_fn(coordinator.data[slug])
        )

    add_new_cars()
    entry.async_on_unload(coordinator.async_add_listener(add_new_cars))


class OdoPlanSensor(CoordinatorEntity[OdoPlanCoordinator], SensorEntity):
    """One number of one car."""

    entity_description: OdoPlanSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: OdoPlanCoordinator, slug: str, description: OdoPlanSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._slug = slug
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{slug}_{description.key}"
        car = coordinator.data[slug]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, slug)},
            name=car.get("name") or slug,
            manufacturer="OdoPlan",
            model=car.get("powertrain"),
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=f"{coordinator.client.url}/cars/{slug}",
        )

    @property
    def available(self) -> bool:
        """Gone when the car was deleted or renamed away in OdoPlan."""
        return super().available and self._slug in self.coordinator.data

    @property
    def native_value(self) -> Any:
        """The number from OdoPlan's latest answer."""
        return self.entity_description.value_fn(self.coordinator.data[self._slug])
