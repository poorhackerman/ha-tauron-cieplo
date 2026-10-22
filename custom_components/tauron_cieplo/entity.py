"""Shared identity and attributes."""

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, NAME, SOURCE_URL
from .parser import select_outage


class TauronEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['street_id']}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data["street_id"])},
            name=f"{NAME} {entry.title}",
            manufacturer="TAURON Ciepło",
            entry_type=None,
            configuration_url=SOURCE_URL,
        )

    @property
    def selected(self):
        return select_outage(self.coordinator.data["outages"], dt_util.utcnow())

    @property
    def extra_state_attributes(self):
        return {
            "source": SOURCE_URL,
            "outages": [
                {
                    key: value.isoformat()
                    if key in ("start", "end") and value
                    else value
                    for key, value in row.items()
                }
                for row in self.coordinator.data["outages"]
            ],
        }
