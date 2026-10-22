"""Client for the public API used by Tauron's outage search."""

import asyncio
import json

import aiohttp

from .const import BASE_URL
from .parser import InvalidResponse, parse_outages


class TauronApi:
    def __init__(self, session):
        self.session = session

    async def request(self, path, **params):
        async with asyncio.timeout(25):
            async with self.session.get(
                f"{BASE_URL}/iapi/{path}", params=params
            ) as response:
                response.raise_for_status()
                try:
                    return json.loads(await response.text())
                except (ValueError, UnicodeError) as err:
                    raise InvalidResponse("Invalid JSON") from err

    async def locations(self, path, **params):
        data = await self.request(path, **params)
        if not isinstance(data, list) or any(
            not isinstance(row, dict)
            or not isinstance(row.get("Name"), str)
            or not row.get("Gaid")
            for row in data
        ):
            raise InvalidResponse("Invalid location list")
        return data

    async def cities(self, query):
        return await self.locations("city/getcities", partName=query)

    async def streets(self, city_id, query):
        return await self.locations(
            "street/GetStreets", ownerGaid=city_id, partName=query
        )

    async def outages(self, street_id):
        return parse_outages(
            await self.request("warmoutage/getoutages", ulica=street_id)
        )


API_ERRORS = (aiohttp.ClientError, TimeoutError, InvalidResponse)
