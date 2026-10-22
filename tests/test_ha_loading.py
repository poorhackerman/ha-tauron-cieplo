"""Load the actual HA modules; API-only tests cannot catch broken HA imports."""

import importlib
import importlib.util
import unittest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

HA_INSTALLED = importlib.util.find_spec("homeassistant") is not None


@unittest.skipUnless(HA_INSTALLED, "Requires Home Assistant (tested in CI on Linux)")
class HomeAssistantLoadingTests(unittest.IsolatedAsyncioTestCase):
    async def test_options_interval_and_validation(self):
        from custom_components.tauron_cieplo.config_flow import (
            TauronConfigFlow,
            TauronOptionsFlow,
        )

        entry = MagicMock()
        entry.options = {}
        flow = TauronConfigFlow.async_get_options_flow(entry)
        flow.hass = MagicMock()
        flow.handler = "test_entry"
        with patch.object(
            TauronOptionsFlow,
            "config_entry",
            new_callable=PropertyMock,
            return_value=entry,
        ):
            form = await flow.async_step_init()
            self.assertEqual(form["data_schema"]({}), {"update_interval": 60})
            for interval in (0, 4, 1441, "bad"):
                result = await flow.async_step_init({"update_interval": interval})
                self.assertEqual(
                    result["errors"], {"update_interval": "invalid_interval"}
                )
            for interval in (5, 60, 1440):
                result = await flow.async_step_init({"update_interval": interval})
                self.assertEqual(result["type"], "create_entry")
                self.assertEqual(result["data"]["update_interval"], interval)
            entry.options = {"update_interval": 120}
            form = await flow.async_step_init()
            self.assertEqual(form["data_schema"]({}), {"update_interval": 120})

    async def test_coordinator_uses_selected_interval(self):
        import tempfile
        from datetime import timedelta

        from custom_components.tauron_cieplo.coordinator import TauronCoordinator
        from homeassistant.core import HomeAssistant

        with tempfile.TemporaryDirectory() as config_dir:
            hass = HomeAssistant(config_dir)
            for options, expected in (
                ({}, 60),
                ({"update_interval": 5}, 5),
                ({"update_interval": 120}, 120),
            ):
                entry = MagicMock()
                entry.data = {"street_id": "1"}
                entry.options = options
                coordinator = TauronCoordinator(hass, entry, MagicMock())
                self.assertEqual(
                    coordinator.update_interval, timedelta(minutes=expected)
                )

    async def test_options_update_reloads_existing_entry(self):
        from custom_components.tauron_cieplo import async_update_options

        hass, entry = MagicMock(), MagicMock()
        entry.entry_id = "existing_street"
        hass.config_entries.async_reload = AsyncMock()
        await async_update_options(hass, entry)
        hass.config_entries.async_reload.assert_awaited_once_with("existing_street")

    async def test_config_flow_and_entity_modules_load(self):
        from homeassistant import config_entries

        for module in ("config_flow", "binary_sensor", "sensor", "coordinator"):
            importlib.import_module(f"custom_components.tauron_cieplo.{module}")
        self.assertIsNotNone(config_entries.HANDLERS.get("tauron_cieplo"))

    async def test_initial_configuration_form(self):
        import tempfile

        from custom_components.tauron_cieplo.config_flow import TauronConfigFlow
        from homeassistant.core import HomeAssistant

        with tempfile.TemporaryDirectory() as config_dir:
            flow = TauronConfigFlow()
            flow.hass = HomeAssistant(config_dir)
            flow.handler = "tauron_cieplo"
            result = await flow.async_step_user()
            self.assertEqual(result["type"], "form")
            self.assertEqual(result["step_id"], "user")
            self.assertEqual(result["errors"], {})

    async def test_street_search_fetches_filtered_results(self):
        from custom_components.tauron_cieplo.api import TauronApi
        from custom_components.tauron_cieplo.config_flow import TauronConfigFlow

        flow = TauronConfigFlow()
        flow.hass = MagicMock()
        flow.handler = "tauron_cieplo"
        flow._city = {"Name": "Katowice", "Gaid": "9"}
        with (
            patch(
                "custom_components.tauron_cieplo.config_flow.async_get_clientsession"
            ),
            patch.object(TauronApi, "streets", new_callable=AsyncMock) as streets,
        ):
            streets.return_value = [{"Name": "ul. Ziołowa", "Gaid": "259696"}]
            result = await flow.async_step_street_search({"street": " Zio "})
        streets.assert_awaited_once_with("9", "Zio")
        self.assertEqual(result["step_id"], "street")
        self.assertEqual(flow._streets, {"259696": "ul. Ziołowa"})
        result = await flow.async_step_street({"search_again": True})
        self.assertEqual(result["step_id"], "street_search")

    async def test_street_search_no_results_and_short_query(self):
        from custom_components.tauron_cieplo.api import TauronApi
        from custom_components.tauron_cieplo.config_flow import TauronConfigFlow

        flow = TauronConfigFlow()
        flow.hass = MagicMock()
        flow.handler = "tauron_cieplo"
        flow._city = {"Name": "Katowice", "Gaid": "9"}
        with (
            patch(
                "custom_components.tauron_cieplo.config_flow.async_get_clientsession"
            ),
            patch.object(TauronApi, "streets", new_callable=AsyncMock) as streets,
        ):
            result = await flow.async_step_street_search({"street": "ab"})
            self.assertEqual(result["errors"], {"street": "too_short"})
            streets.assert_not_awaited()
            streets.return_value = []
            result = await flow.async_step_street_search({"street": "missing"})
            self.assertEqual(result["errors"], {"street": "not_found"})

    async def test_active_sensor_and_boundary_timer(self):
        from datetime import UTC, datetime, timedelta

        from custom_components.tauron_cieplo.binary_sensor import TauronActiveOutage

        now = datetime(2026, 10, 22, 12, tzinfo=UTC)
        start, end = now + timedelta(minutes=1), now + timedelta(minutes=2)
        coordinator = MagicMock()
        coordinator.data = {"present": True, "outages": [{"start": start, "end": end}]}
        entry = MagicMock()
        entry.data = {"street_id": "1"}
        sensor = TauronActiveOutage(coordinator, entry, "active_outage")
        sensor.hass = MagicMock()
        target = "custom_components.tauron_cieplo.binary_sensor"
        with (
            patch(f"{target}.dt_util.utcnow", return_value=now),
            patch(f"{target}.async_track_point_in_utc_time") as track,
        ):
            self.assertFalse(sensor.is_on)
            sensor._schedule_boundary()
            self.assertEqual(track.call_args.args[2], start)
            cancel = track.return_value
            coordinator.data["outages"][0]["start"] = now - timedelta(minutes=1)
            sensor._schedule_boundary()
            cancel.assert_called_once()
            self.assertTrue(sensor.is_on)
            self.assertEqual(track.call_args.args[2], end)
            sensor._cancel_timer()
        with patch(f"{target}.dt_util.utcnow", return_value=end):
            self.assertFalse(sensor.is_on)
