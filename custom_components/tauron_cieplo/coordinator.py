"""Shared polling for all entities of one street."""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import API_ERRORS
from .const import DOMAIN


class TauronCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, api):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=5),
        )
        self.api = api
        self.street_id = entry.data["street_id"]

    async def _async_update_data(self):
        try:
            return await self.api.outages(self.street_id)
        except API_ERRORS as err:
            raise UpdateFailed(f"Cannot fetch TAURON outages: {err}") from err
