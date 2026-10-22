"""Whether Tauron publishes an outage notice for this street."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .entity import TauronEntity
from .parser import active_outage


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            TauronOutage(entry.runtime_data, entry, "outage"),
            TauronActiveOutage(entry.runtime_data, entry, "active_outage"),
        ]
    )


class TauronOutage(TauronEntity, BinarySensorEntity):
    _attr_translation_key = "outage"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        return self.coordinator.data["present"]


class TauronActiveOutage(TauronEntity, BinarySensorEntity):
    """Evaluate current time locally, including between API refreshes."""

    _attr_translation_key = "active_outage"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _cancel_boundary = None

    @property
    def is_on(self):
        return active_outage(self.coordinator.data["outages"], dt_util.utcnow())

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(self._cancel_timer)
        self._schedule_boundary()

    @callback
    def _cancel_timer(self):
        if self._cancel_boundary:
            self._cancel_boundary()
            self._cancel_boundary = None

    @callback
    def _schedule_boundary(self):
        self._cancel_timer()
        now = dt_util.utcnow()
        boundaries = [
            value
            for row in self.coordinator.data["outages"]
            for key in ("start", "end")
            if (value := row[key]) is not None and value > now
        ]
        if boundaries:
            self._cancel_boundary = async_track_point_in_utc_time(
                self.hass, self._boundary_reached, min(boundaries)
            )

    @callback
    def _boundary_reached(self, now):
        self._cancel_boundary = None
        self._schedule_boundary()
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self):
        self._schedule_boundary()
        super()._handle_coordinator_update()
