"""Configure city and street using Tauron's own address identifiers."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import API_ERRORS, TauronApi
from .const import CONF_CITY, CONF_STREET, CONF_STREET_ID, DOMAIN


class TauronConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._cities = {}
        self._streets = {}
        self._city = None

    @property
    def api(self):
        return TauronApi(async_get_clientsession(self.hass))

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            query = user_input[CONF_CITY].strip()
            if len(query) < 3:
                errors[CONF_CITY] = "too_short"
            else:
                try:
                    rows = await self.api.cities(query)
                    self._cities = {str(r["Gaid"]): r for r in rows}
                except API_ERRORS:
                    errors["base"] = "cannot_connect"
                else:
                    if self._cities:
                        return await self.async_step_city()
                    errors[CONF_CITY] = "not_found"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_CITY): str}),
            errors=errors,
        )

    async def async_step_city(self, user_input=None):
        errors = {}
        if user_input is not None:
            city_id = user_input[CONF_CITY]
            if city_id not in self._cities:
                errors["base"] = "not_found"
            else:
                self._city = self._cities[city_id]
                return await self.async_step_street_search()
        choices = {
            key: f"{r['Name']} ({r.get('ProvinceName', '')}, {r.get('DistrictName', '')})"
            for key, r in self._cities.items()
        }
        return self.async_show_form(
            step_id="city",
            data_schema=vol.Schema({vol.Required(CONF_CITY): vol.In(choices)}),
            errors=errors,
        )

    async def async_step_street_search(self, user_input=None):
        errors = {}
        if user_input is not None:
            query = user_input[CONF_STREET].strip()
            if len(query) < 3:
                errors[CONF_STREET] = "too_short"
            else:
                try:
                    rows = await self.api.streets(str(self._city["Gaid"]), query)
                except API_ERRORS:
                    errors["base"] = "cannot_connect"
                else:
                    self._streets = {str(r["Gaid"]): r["Name"] for r in rows}
                    if self._streets:
                        return await self.async_step_street()
                    errors[CONF_STREET] = "not_found"
        return self.async_show_form(
            step_id="street_search",
            data_schema=vol.Schema({vol.Required(CONF_STREET): str}),
            errors=errors,
        )

    async def async_step_street(self, user_input=None):
        errors = {}
        if user_input is not None:
            if user_input.get("search_again"):
                return await self.async_step_street_search()
            street_id = user_input.get(CONF_STREET)
            if street_id not in self._streets:
                errors["base"] = "not_found"
            else:
                await self.async_set_unique_id(street_id)
                self._abort_if_unique_id_configured()
                try:
                    await self.api.outages(street_id)
                except API_ERRORS:
                    errors["base"] = "cannot_connect"
                else:
                    street = self._streets[street_id]
                    return self.async_create_entry(
                        title=f"{self._city['Name']}, {street}",
                        data={
                            CONF_CITY: self._city["Name"],
                            "city_id": str(self._city["Gaid"]),
                            CONF_STREET: street,
                            CONF_STREET_ID: street_id,
                        },
                    )
        return self.async_show_form(
            step_id="street",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_STREET): vol.In(self._streets),
                    vol.Optional("search_again", default=False): bool,
                }
            ),
            errors=errors,
        )
