"""Load the actual HA modules; API-only tests cannot catch broken HA imports."""

import importlib
import importlib.util
import unittest

HA_INSTALLED = importlib.util.find_spec("homeassistant") is not None


@unittest.skipUnless(HA_INSTALLED, "Requires Home Assistant (tested in CI on Linux)")
class HomeAssistantLoadingTests(unittest.IsolatedAsyncioTestCase):
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
