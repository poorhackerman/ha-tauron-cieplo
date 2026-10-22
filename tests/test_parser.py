"""Regression tests, including two real Tauron responses captured 2026-10-22."""

import importlib.util
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "parser", ROOT / "custom_components/tauron_cieplo/parser.py"
)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)


class ParserTests(unittest.TestCase):
    def fixture(self, name):
        return json.loads(
            (ROOT / f"tests/fixtures/{name}.json").read_text(encoding="utf-8")
        )

    def test_real_outage(self):
        result = parser.parse_outages(self.fixture("outage"))
        self.assertTrue(result["present"])
        row = result["outages"][0]
        self.assertEqual(row["start"].isoformat(), "2026-10-21T01:00:00+02:00")
        self.assertEqual(row["end"].isoformat(), "2026-10-22T10:00:00+02:00")

    def test_real_no_outage(self):
        self.assertEqual(
            parser.parse_outages(self.fixture("no_outage")),
            {"present": False, "outages": []},
        )

    def test_invalid_response_is_not_clear(self):
        for payload in (
            None,
            [],
            {},
            {"Outages": {}},
            {"Outages": {"Present": "false"}},
            {"Outages": {"Present": True}},
            {"Outages": {"Present": True, "outageInfo": {"info": []}}},
        ):
            with (
                self.subTest(payload=payload),
                self.assertRaises(parser.InvalidResponse),
            ):
                parser.parse_outages(payload)

    def test_unknown_dates_keep_notice(self):
        data = {
            "Outages": {
                "Present": True,
                "outageInfo": {"info": {"reply": "Awaria", "details": "Do odwołania"}},
            }
        }
        result = parser.parse_outages(data)
        self.assertTrue(result["present"])
        self.assertIsNone(result["outages"][0]["end"])

    def test_bad_or_reversed_dates(self):
        for text in (
            "od 32.10.2026 godz. 12:00 do 22.10.2026 godz. 13:00",
            "od 23.10.2026 godz. 12:00 do 22.10.2026 godz. 13:00",
            "od 12:00 do 15:00",
        ):
            self.assertEqual(parser.parse_period(text), (None, None))

    def test_winter_timezone(self):
        start, end = parser.parse_period(
            "od 01.12.2026 godz. 10:00 do 01.12.2026 godz. 12:00"
        )
        self.assertEqual(start.utcoffset().total_seconds(), 3600)
        self.assertEqual(end.utcoffset().total_seconds(), 3600)

    def test_html(self):
        self.assertEqual(
            parser.clean("<b>Awaria</b><br>Ciepło &amp; woda"), "Awaria Ciepło & woda"
        )

    def test_multiple_notices_selection(self):
        def row(day):
            start, end = parser.parse_period(
                f"od {day}.10.2026 godz. 01:00 do {day}.10.2026 godz. 23:00"
            )
            return {"start": start, "end": end}

        past, current, future = row(20), row(22), row(25)
        now = datetime(2026, 10, 22, 12, tzinfo=UTC)
        self.assertIs(parser.select_outage([future, past, current], now), current)
        self.assertIs(parser.select_outage([future, past], now), future)
        self.assertIs(parser.select_outage([past], now), past)
        self.assertIsNone(parser.select_outage([], now))


if __name__ == "__main__":
    unittest.main()
