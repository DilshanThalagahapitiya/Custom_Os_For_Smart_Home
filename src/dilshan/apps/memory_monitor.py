"""Memory Monitor: live RAM, cache, swap, ZRAM and memory pressure."""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from dilshan import memory  # noqa: E402

REFRESH_SECONDS = 2


class Row:
    """One labelled bar with a value text."""

    def __init__(self, grid: Gtk.Grid, line: int, title: str):
        self.bar = Gtk.LevelBar(hexpand=True)
        self.value = Gtk.Label(xalign=1)
        title_label = Gtk.Label(label=title, xalign=0)
        for column, widget in enumerate((title_label, self.bar, self.value)):
            grid.attach(widget, column, line, 1, 1)

    def set(self, fraction: float, text: str) -> None:
        self.bar.set_value(max(0.0, min(1.0, fraction)))
        self.value.set_text(text)


class MemoryMonitor(Gtk.Window):
    def __init__(self):
        super().__init__(title="Memory Monitor")
        self.set_default_size(460, 240)
        self.set_border_width(16)
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        self.add(grid)
        self.ram = Row(grid, 0, "RAM used")
        self.cache = Row(grid, 1, "Cached")
        self.swap = Row(grid, 2, "Swap")
        self.zram = Row(grid, 3, "ZRAM")
        self.pressure = Row(grid, 4, "Pressure")
        self.refresh()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self.refresh)

    def refresh(self) -> bool:
        s = memory.read_summary()
        fmt = memory.format_size
        self.ram.set(s.used / s.total, f"{fmt(s.used)} / {fmt(s.total)}  (available {fmt(s.available)})")
        self.cache.set(s.cached / s.total, fmt(s.cached))
        self.swap.set(s.swap_used / s.swap_total if s.swap_total else 0,
                      f"{fmt(s.swap_used)} / {fmt(s.swap_total)}" if s.swap_total else "off")

        z = memory.read_zram()
        if z and z.original:
            self.zram.set(z.memory_used / (s.total * 1024),
                          f"{fmt(z.original / 1024)} stored in {fmt(z.memory_used / 1024)}  ({z.ratio:.1f}:1)")
        else:
            self.zram.set(0, "not in use")

        p = memory.read_pressure()
        self.pressure.set((p or 0) / 100, f"{p:.1f}%" if p is not None else "not supported")
        return True  # keep the timer running


def main() -> None:
    window = MemoryMonitor()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
