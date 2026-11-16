import tempfile
import unittest
from pathlib import Path

from dilshan import power

PPD_OUTPUT = """  performance:
    Driver:     intel_pstate

* balanced:
    Driver:     intel_pstate

  power-saver:
    Driver:     intel_pstate
"""


def make_battery(root: Path, name: str, **files: str) -> None:
    d = root / name
    d.mkdir()
    for key, value in files.items():
        (d / key).write_text(value + "\n")


class PowerTests(unittest.TestCase):
    def test_parse_profiles(self):
        names, active = power.parse_profiles(PPD_OUTPUT)
        self.assertEqual(names, ["performance", "balanced", "power-saver"])
        self.assertEqual(active, "balanced")

    def test_battery_with_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_battery(root, "BAT0", type="Battery", status="Discharging", capacity="80",
                         energy_full="30000", energy_full_design="40000")
            make_battery(root, "AC", type="Mains")
            batteries = power.list_batteries(root)
        self.assertEqual(len(batteries), 1)
        self.assertEqual(batteries[0].percent, 80)
        self.assertEqual(batteries[0].health, 75.0)

    def test_battery_without_design_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_battery(root, "BAT0", type="Battery", status="Full", capacity="100")
            self.assertIsNone(power.list_batteries(root)[0].health)

    def test_missing_directory(self):
        self.assertEqual(power.list_batteries(Path("/nonexistent")), [])


if __name__ == "__main__":
    unittest.main()
