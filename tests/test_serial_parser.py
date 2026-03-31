# SPDX-License-Identifier: MIT
"""
tests/test_serial_parser.py
Unit tests for Project Nira serial protocol parsing logic.
Run with: python -m unittest -v
"""

import json
import math
import unittest


# -- Helpers mirroring nira_gui.py DataStore.push() logic ----------------------

def parse_frame(line: str) -> dict:
    """Parse a JSON serial frame from the device."""
    return json.loads(line.strip())


def compute_mp_index(deltas: list[float]) -> float:
    """Replicate firmware mp_index formula."""
    return math.sqrt(sum(d**2 for d in deltas) / len(deltas))


# -- Tests ---------------------------------------------------------------------

class TestSampleFrameParsing(unittest.TestCase):
    SAMPLE_LINE = (
        '{"ts":12345,"n":42,'
        '"ch0":12.3401,"ch1":12.1003,"ch2":11.9812,"ch3":12.0540,'
        '"d0":0.0021,"d1":-0.0132,"d2":0.0088,"d3":-0.0044,'
        '"temp":28.5,"bat_mv":3820,"mp_index":0.00821,"mode":"sample"}'
    )

    def test_all_fields_present(self):
        obj = parse_frame(self.SAMPLE_LINE)
        required = ["ts","n","ch0","ch1","ch2","ch3",
                    "d0","d1","d2","d3","temp","bat_mv","mp_index","mode"]
        for field in required:
            self.assertIn(field, obj, f"Missing field: {field}")

    def test_ts_is_uint(self):
        obj = parse_frame(self.SAMPLE_LINE)
        self.assertIsInstance(obj["ts"], int)
        self.assertGreaterEqual(obj["ts"], 0)

    def test_channel_values_float(self):
        obj = parse_frame(self.SAMPLE_LINE)
        for ch in ["ch0","ch1","ch2","ch3"]:
            self.assertIsInstance(obj[ch], float)

    def test_mp_index_nonnegative(self):
        obj = parse_frame(self.SAMPLE_LINE)
        self.assertGreaterEqual(obj["mp_index"], 0.0)

    def test_mp_index_formula(self):
        obj = parse_frame(self.SAMPLE_LINE)
        deltas = [obj[f"d{i}"] for i in range(4)]
        expected = compute_mp_index(deltas)
        self.assertLess(abs(obj["mp_index"] - expected), 1e-4)

    def test_mode_is_sample(self):
        obj = parse_frame(self.SAMPLE_LINE)
        self.assertEqual(obj["mode"], "sample")


class TestStatusFrames(unittest.TestCase):
    def test_boot_frame(self):
        line = '{"status":"boot","fw":"nira-v1.1","proto":"nira-serial-v1"}'
        obj = parse_frame(line)
        self.assertEqual(obj["status"], "boot")
        self.assertIn("fw", obj)
        self.assertIn("proto", obj)

    def test_zero_done_frame(self):
        line = '{"status":"zero_done","base_pF":[12.34,12.10,11.98,12.05]}'
        obj = parse_frame(line)
        self.assertEqual(obj["status"], "zero_done")
        self.assertEqual(len(obj["base_pF"]), 4)

    def test_rate_set_frame(self):
        line = '{"status":"rate_set","interval_ms":500}'
        obj = parse_frame(line)
        self.assertEqual(obj["status"], "rate_set")
        self.assertEqual(obj["interval_ms"], 500)


class TestErrorFrames(unittest.TestCase):
    def test_sensor_error(self):
        line = '{"error":"sensor_read_failed"}'
        obj = parse_frame(line)
        self.assertIn("error", obj)

    def test_unknown_cmd_error(self):
        line = '{"error":"unknown_cmd","cmd":"CMD:BLAH"}'
        obj = parse_frame(line)
        self.assertEqual(obj["error"], "unknown_cmd")
        self.assertIn("cmd", obj)


class TestMpIndex(unittest.TestCase):
    def test_zero_deltas_gives_zero_index(self):
        self.assertEqual(compute_mp_index([0.0, 0.0, 0.0, 0.0]), 0.0)

    def test_symmetric_deltas(self):
        idx = compute_mp_index([0.1, -0.1, 0.1, -0.1])
        self.assertLess(abs(idx - 0.1), 1e-9)

    def test_danger_threshold(self):
        DANGER_THRESH = 0.10
        # Deltas that produce mp_index just above threshold
        deltas = [0.11, 0.11, 0.11, 0.11]
        self.assertGreater(compute_mp_index(deltas), DANGER_THRESH)


if __name__ == "__main__":
    unittest.main()
