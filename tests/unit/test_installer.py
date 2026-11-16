import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dilshan import installer
from dilshan.installer import InstallError, Kind


def make_flutter_tar(path: Path) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, data in (("myapp/myapp", b"\x7fELFxxxx"), ("myapp/lib/libflutter_linux_gtk.so", b"so"),
                           ("myapp/data/flutter_assets/AssetManifest.json", b"{}")):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.apps, self.desktop = self.dir / "apps", self.dir / "desktop"

    def tearDown(self):
        self.tmp.cleanup()

    def test_detect_by_extension(self):
        self.assertIs(installer.detect_kind(Path("Setup.EXE")), Kind.WINDOWS)
        self.assertIs(installer.detect_kind(Path("a.deb")), Kind.DEB)
        self.assertIs(installer.detect_kind(Path("a.flatpak")), Kind.FLATPAK)
        self.assertIs(installer.detect_kind(Path("a.AppImage")), Kind.APPIMAGE)

    def test_flutter_archive_install(self):
        archive = self.dir / "myapp.tar.gz"
        make_flutter_tar(archive)
        self.assertIs(installer.detect_kind(archive), Kind.FLUTTER)
        result = installer.install(archive, apps_dir=self.apps, desktop_dir=self.desktop)
        self.assertIs(result.kind, Kind.FLUTTER)
        program = self.apps / "myapp/myapp/myapp"
        self.assertTrue(program.exists())
        entry = (self.desktop / "dilshan-myapp.desktop").read_text()
        self.assertIn(f'Exec="{program}"', entry)

    def test_archive_without_flutter_is_unknown(self):
        archive = self.dir / "other.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            info = tarfile.TarInfo("readme.txt")
            tar.addfile(info, io.BytesIO(b""))
        self.assertIs(installer.detect_kind(archive), Kind.UNKNOWN)
        with self.assertRaises(InstallError):
            installer.install(archive, apps_dir=self.apps, desktop_dir=self.desktop)

    def test_path_traversal_rejected(self):
        archive = self.dir / "evil.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            info = tarfile.TarInfo("../escape.txt")
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(InstallError):
            installer.safe_extract(archive, self.dir / "out")

    def test_windows_needs_wine(self):
        exe = self.dir / "setup.exe"
        exe.write_bytes(b"MZ")
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(installer.MissingTool):
                installer.install(exe, apps_dir=self.apps, desktop_dir=self.desktop)

    def test_windows_runs_wine_and_reports_failure(self):
        exe = self.dir / "setup.exe"
        exe.write_bytes(b"MZ")
        calls = []
        with mock.patch("shutil.which", return_value="/usr/bin/wine"):
            installer.install(exe, runner=lambda c: calls.append(c) or 0,
                              apps_dir=self.apps, desktop_dir=self.desktop)
            self.assertEqual(calls[0][0], "wine")
            with self.assertRaises(InstallError):
                installer.install(exe, runner=lambda c: 1, apps_dir=self.apps, desktop_dir=self.desktop)

    def test_deb_uses_pkexec_apt(self):
        deb = self.dir / "tool.deb"
        deb.write_bytes(b"x")
        calls = []
        installer.install(deb, runner=lambda c: calls.append(c) or 0)
        self.assertEqual(calls[0][:3], ["pkexec", "apt-get", "install"])

    def test_appimage_is_copied_and_executable(self):
        image = self.dir / "Tool.AppImage"
        image.write_bytes(b"x")
        installer.install(image, apps_dir=self.apps, desktop_dir=self.desktop)
        self.assertTrue((self.apps / "Tool.AppImage").stat().st_mode & 0o100)


if __name__ == "__main__":
    unittest.main()
