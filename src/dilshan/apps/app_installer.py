"""App Installer: drop or choose a file (Flutter bundle, .exe/.msi, .deb, .flatpak, .AppImage)."""
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gdk, Gtk  # noqa: E402

from dilshan import installer  # noqa: E402

UPLOADS = Path.home() / "Uploads"
FILTER_HELP = "Flutter bundle (.tar.gz, .zip), Windows (.exe, .msi), .deb, .flatpak, .AppImage"


class AppInstaller(Gtk.Window):
    def __init__(self):
        super().__init__(title="App Installer")
        self.set_default_size(480, 260)
        self.set_border_width(16)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(box)

        drop = Gtk.Label(label="Drop a file here\n\n" + FILTER_HELP, justify=Gtk.Justification.CENTER)
        drop.set_vexpand(True)
        box.pack_start(drop, True, True, 0)
        choose = Gtk.Button(label="Choose file...")
        choose.connect("clicked", self.on_choose)
        box.pack_start(choose, False, False, 0)
        self.status = Gtk.Label(xalign=0, wrap=True)
        box.pack_start(self.status, False, False, 0)

        self.drag_dest_set(Gtk.DestDefaults.ALL, [Gtk.TargetEntry.new("text/uri-list", 0, 0)],
                           Gdk.DragAction.COPY)
        self.connect("drag-data-received", self.on_drop)

    def on_choose(self, _button) -> None:
        dialog = Gtk.FileChooserDialog(title="Choose an app file", parent=self,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Install", Gtk.ResponseType.OK)
        if UPLOADS.is_dir():
            dialog.set_current_folder(str(UPLOADS))
        if dialog.run() == Gtk.ResponseType.OK:
            self.start_install(Path(dialog.get_filename()))
        dialog.destroy()

    def on_drop(self, _widget, _context, _x, _y, data, _info, _time) -> None:
        uris = data.get_uris()
        if uris:
            self.start_install(Path(GLib.filename_from_uri(uris[0])[0]))

    def start_install(self, path: Path) -> None:
        self.status.set_text(f"Installing {path.name}...")
        threading.Thread(target=self.worker, args=(path,), daemon=True).start()

    def worker(self, path: Path) -> None:
        try:
            message = installer.install(path).message
        except installer.MissingTool as exc:
            GLib.idle_add(self.offer_tool, exc.tool, path)
            return
        except installer.InstallError as exc:
            message = f"Failed: {exc}"
        GLib.idle_add(self.status.set_text, message)

    def offer_tool(self, tool: str, path: Path) -> None:
        if tool == "wine":
            dialog = Gtk.MessageDialog(parent=self, message_type=Gtk.MessageType.QUESTION,
                                       buttons=Gtk.ButtonsType.YES_NO,
                                       text="Wine is needed to run Windows apps. Install it now?")
            dialog.format_secondary_text("Wine is optional and uses about 300 MB. "
                                         "Not every Windows app will work.")
            if dialog.run() == Gtk.ResponseType.YES:
                dialog.destroy()
                self.status.set_text("Installing Wine...")
                threading.Thread(target=self.install_wine_then, args=(path,), daemon=True).start()
                return
            dialog.destroy()
        self.status.set_text(f"{tool} is not installed.")

    def install_wine_then(self, path: Path) -> None:
        try:
            installer.install_wine()
        except installer.InstallError as exc:
            GLib.idle_add(self.status.set_text, f"Failed: {exc}")
            return
        self.worker(path)


def main() -> None:
    window = AppInstaller()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
