"""Whether Tauron publishes an outage notice for this street."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .entity import TauronEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([TauronOutage(entry.runtime_data, entry, "outage")])


class TauronOutage(TauronEntity, BinarySensorEntity):
    _attr_translation_key = "outage"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        return self.coordinator.data["present"]
