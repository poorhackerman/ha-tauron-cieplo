"""Notice text and the selected outage's published time range."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .entity import TauronEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            TauronSensor(entry.runtime_data, entry, key)
            for key in ("start", "end", "message")
        ]
    )


class TauronSensor(TauronEntity, SensorEntity):
    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator, entry, key)
        self.key = key
        self._attr_translation_key = key
        if key in ("start", "end"):
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        else:
            self._attr_icon = "mdi:message-alert-outline"

    @property
    def native_value(self):
        row = self.selected
        if self.key == "message":
            return (
                f"{row['reply']} {row['details']}".strip()
                if row
                else "Brak informacji o awarii"
            )[:255]
        return row[self.key] if row else None
