"""Linux memory statistics.

Parsing functions take text and are pure, so they can be unit tested.
The read_* functions only fetch text from /proc and /sys.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROC = Path("/proc")
SYS = Path("/sys")


@dataclass(frozen=True)
class MemorySummary:
    """All values in kibibytes."""
    total: int
    available: int
    cached: int
    swap_total: int
    swap_free: int

    @property
    def used(self) -> int:
        return self.total - self.available

    @property
    def swap_used(self) -> int:
        return self.swap_total - self.swap_free


@dataclass(frozen=True)
class ZramStats:
    """Sizes in bytes."""
    original: int
    compressed: int
    memory_used: int

    @property
    def ratio(self) -> float:
        return self.original / self.compressed if self.compressed else 0.0


def format_size(kib: float) -> str:
    """Format a size given in KiB, e.g. 2048 -> '2.0 MiB'."""
    value = float(kib)
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def parse_meminfo(text: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts:
            values[key] = int(parts[0])
    return values


def summarize(meminfo: dict[str, int]) -> MemorySummary:
    return MemorySummary(
        total=meminfo["MemTotal"],
        available=meminfo.get("MemAvailable", meminfo.get("MemFree", 0)),
        cached=meminfo.get("Cached", 0) + meminfo.get("Buffers", 0),
        swap_total=meminfo.get("SwapTotal", 0),
        swap_free=meminfo.get("SwapFree", 0),
    )


def parse_pressure(text: str) -> dict[str, dict[str, float]]:
    """Parse /proc/pressure/memory into {'some': {'avg10': 0.0, ...}, 'full': {...}}."""
    result: dict[str, dict[str, float]] = {}
    for line in text.splitlines():
        kind, *fields = line.split()
        result[kind] = {k: float(v) for k, v in (f.split("=") for f in fields)}
    return result


def parse_zram_mm_stat(text: str) -> ZramStats:
    original, compressed, used = (int(x) for x in text.split()[:3])
    return ZramStats(original, compressed, used)


def read_summary() -> MemorySummary:
    return summarize(parse_meminfo((PROC / "meminfo").read_text()))


def read_pressure() -> Optional[float]:
    """Share of the last 10 s some task stalled on memory (percent), or None if unsupported."""
    try:
        return parse_pressure((PROC / "pressure/memory").read_text())["some"]["avg10"]
    except (OSError, KeyError):
        return None


def read_zram(device: str = "zram0") -> Optional[ZramStats]:
    try:
        return parse_zram_mm_stat((SYS / "block" / device / "mm_stat").read_text())
    except (OSError, ValueError):
        return None
