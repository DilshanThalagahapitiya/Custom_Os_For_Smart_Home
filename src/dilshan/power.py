"""Battery information and power profiles (via power-profiles-daemon)."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

POWER_SUPPLY = Path("/sys/class/power_supply")


class PowerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Battery:
    name: str
    percent: int
    status: str                 # Charging, Discharging, Full, ...
    health: Optional[float]     # full capacity / design capacity, in percent


def _read_int(path: Path) -> Optional[int]:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def read_battery(directory: Path) -> Optional[Battery]:
    """Read one /sys/class/power_supply/BAT* directory. Returns None if it is not a battery."""
    try:
        if (directory / "type").read_text().strip() != "Battery":
            return None
        status = (directory / "status").read_text().strip()
    except OSError:
        return None
    percent = _read_int(directory / "capacity")
    if percent is None:
        return None
    health = None
    for full, design in (("energy_full", "energy_full_design"), ("charge_full", "charge_full_design")):
        f, d = _read_int(directory / full), _read_int(directory / design)
        if f and d:
            health = round(f / d * 100, 1)
            break
    return Battery(directory.name, percent, status, health)


def list_batteries(root: Path = POWER_SUPPLY) -> list[Battery]:
    if not root.is_dir():
        return []
    found = (read_battery(d) for d in sorted(root.iterdir()))
    return [b for b in found if b]


def parse_profiles(output: str) -> tuple[list[str], Optional[str]]:
    """Parse `powerprofilesctl list` into (profile names, active profile)."""
    names: list[str] = []
    active = None
    for line in output.splitlines():
        if line.startswith("    ") or not line.rstrip().endswith(":"):
            continue
        name = line.strip().lstrip("*").strip().rstrip(":")
        names.append(name)
        if line.lstrip().startswith("*"):
            active = name
    return names, active


def _ctl(*args: str) -> str:
    try:
        done = subprocess.run(["powerprofilesctl", *args], capture_output=True,
                              text=True, timeout=10, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PowerError(f"powerprofilesctl failed: {exc}") from exc
    return done.stdout


def get_profiles() -> tuple[list[str], Optional[str]]:
    return parse_profiles(_ctl("list"))


def set_profile(name: str) -> None:
    _ctl("set", name)
