"""Shared polling for all entities of one street."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import API_ERRORS
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    RETRY_UPDATE_INTERVAL,
)


class TauronCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, api):
        self._normal_update_interval = timedelta(
            minutes=entry.options.get(
                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
            )
        )
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
            update_interval=self._normal_update_interval,
        )
        self.api = api
        self.street_id = entry.data["street_id"]

    async def _async_update_data(self):
        try:
            data = await self.api.outages(self.street_id)
        except API_ERRORS as err:
            self.update_interval = timedelta(minutes=RETRY_UPDATE_INTERVAL)
            raise UpdateFailed(f"Cannot fetch TAURON outages: {err}") from err
        self.update_interval = self._normal_update_interval
        return data
