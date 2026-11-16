"""Power Settings: battery status and power profile (power saver / balanced / performance)."""
import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from dilshan import power  # noqa: E402

LABELS = {"power-saver": "Power saver", "balanced": "Balanced", "performance": "Performance"}


class PowerSettings(Gtk.Window):
    def __init__(self):
        super().__init__(title="Power Settings")
        self.set_default_size(420, 280)
        self.set_border_width(16)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(box)

        self.battery_label = Gtk.Label(xalign=0)
        box.pack_start(self.battery_label, False, False, 0)
        box.pack_start(Gtk.Label(label="Power mode", xalign=0), False, False, 0)
        self.message = Gtk.Label(xalign=0)

        self._build_profiles(box)

        more = Gtk.Button(label="Screen timeout, lid and sleep...")
        more.connect("clicked", lambda _b: subprocess.Popen(["xfce4-power-manager-settings"]))
        box.pack_end(more, False, False, 0)
        box.pack_end(self.message, False, False, 0)

        self.refresh_battery()
        GLib.timeout_add_seconds(10, self.refresh_battery)

    def _build_profiles(self, box: Gtk.Box) -> None:
        try:
            names, active = power.get_profiles()
        except power.PowerError as exc:
            self.message.set_text(f"Power modes unavailable: {exc}")
            return
        group = None
        for name in names:
            radio = Gtk.RadioButton.new_with_label_from_widget(group, LABELS.get(name, name))
            group = group or radio
            radio.set_active(name == active)
            radio.connect("toggled", self.on_profile_toggled, name)
            box.pack_start(radio, False, False, 0)

    def on_profile_toggled(self, radio: Gtk.RadioButton, name: str) -> None:
        if not radio.get_active():
            return
        try:
            power.set_profile(name)
            self.message.set_text("")
        except power.PowerError as exc:
            self.message.set_text(str(exc))

    def refresh_battery(self) -> bool:
        batteries = power.list_batteries()
        if not batteries:
            self.battery_label.set_text("No battery detected (desktop computer)")
        else:
            lines = []
            for b in batteries:
                health = f", health {b.health}%" if b.health is not None else ""
                lines.append(f"{b.name}: {b.percent}% ({b.status}{health})")
            self.battery_label.set_text("\n".join(lines))
        return True


def main() -> None:
    window = PowerSettings()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
