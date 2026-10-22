"""Exercise HTTP request parameters and failures without importing HA."""

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import aiohttp

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "tauron_api_tests"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "custom_components/tauron_cieplo")]
sys.modules[PACKAGE] = package
spec = importlib.util.spec_from_file_location(
    f"{PACKAGE}.api", ROOT / "custom_components/tauron_cieplo/api.py"
)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class Response:
    def __init__(self, payload, error=None):
        self.payload, self.error = payload, error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def raise_for_status(self):
        if self.error:
            raise self.error

    async def text(self):
        return self.payload


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_outage_request(self):
        payload = (ROOT / "tests/fixtures/outage.json").read_text(encoding="utf-8")
        session = MagicMock()
        session.get.return_value = Response(payload)
        result = await api.TauronApi(session).outages("254514")
        self.assertTrue(result["present"])
        session.get.assert_called_once_with(
            "https://cieplo.tauron.pl/iapi/warmoutage/getoutages",
            params={"ulica": "254514"},
        )

    async def test_address_requests(self):
        session = MagicMock()
        session.get.return_value = Response(
            json.dumps([{"Name": "Katowice", "Gaid": "9"}])
        )
        client = api.TauronApi(session)
        await client.cities("Katowice")
        session.get.assert_called_with(
            "https://cieplo.tauron.pl/iapi/city/getcities",
            params={"partName": "Katowice"},
        )
        await client.streets("9", "Zio")
        session.get.assert_called_with(
            "https://cieplo.tauron.pl/iapi/street/GetStreets",
            params={"ownerGaid": "9", "partName": "Zio"},
        )

    async def test_bad_json_and_schema(self):
        for payload in (
            "<html>Server error</html>",
            "null",
            "{}",
            '{"Outages":{"Present":"false"}}',
        ):
            session = MagicMock()
            session.get.return_value = Response(payload)
            with self.subTest(payload=payload), self.assertRaises(api.InvalidResponse):
                await api.TauronApi(session).outages("1")

    async def test_http_error(self):
        session = MagicMock()
        session.get.return_value = Response("{}", aiohttp.ClientError("503"))
        with self.assertRaises(aiohttp.ClientError):
            await api.TauronApi(session).outages("1")

    async def test_timeout(self):
        session = MagicMock()
        session.get.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            await api.TauronApi(session).outages("1")

    async def test_bad_location_list(self):
        for payload in ({}, [None], [{"Name": "City"}]):
            session = MagicMock()
            session.get.return_value = Response(json.dumps(payload))
            with self.assertRaises(api.InvalidResponse):
                await api.TauronApi(session).cities("City")
