"""Install an app from a single file: Flutter Linux bundle, Windows .exe/.msi, .deb, .flatpak, .AppImage.

Every external command goes through an injectable runner so the logic is testable.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tarfile
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

APPS_DIR = Path.home() / "Applications"
DESKTOP_DIR = Path.home() / ".local/share/applications"

Runner = Callable[[list], int]


class Kind(Enum):
    FLUTTER = "Flutter app"
    WINDOWS = "Windows app"
    DEB = "Debian package"
    FLATPAK = "Flatpak"
    APPIMAGE = "AppImage"
    UNKNOWN = "Unknown"


class InstallError(RuntimeError):
    pass


class MissingTool(InstallError):
    def __init__(self, tool: str):
        super().__init__(f"{tool} is not installed")
        self.tool = tool


@dataclass(frozen=True)
class InstallResult:
    kind: Kind
    message: str


def run_command(cmd: list) -> int:
    return subprocess.run(cmd).returncode


# ---------- detection ----------

def _archive_names(path: Path) -> list:
    try:
        if tarfile.is_tarfile(path):
            with tarfile.open(path) as tar:
                return tar.getnames()
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                return zf.namelist()
    except (OSError, tarfile.TarError, zipfile.BadZipFile):
        pass
    return []


def detect_kind(path: Path) -> Kind:
    name = path.name.lower()
    if name.endswith((".exe", ".msi")):
        return Kind.WINDOWS
    if name.endswith(".deb"):
        return Kind.DEB
    if name.endswith((".flatpak", ".flatpakref")):
        return Kind.FLATPAK
    if name.endswith(".appimage"):
        return Kind.APPIMAGE
    names = _archive_names(path)
    if any("data/flutter_assets" in n for n in names):
        return Kind.FLUTTER
    return Kind.UNKNOWN


# ---------- helpers ----------

def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "app"


def write_desktop_entry(name: str, exec_line: str, directory: Path,
                        icon: str = "application-x-executable") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    entry = directory / f"dilshan-{safe_name(name)}.desktop"
    entry.write_text(
        "[Desktop Entry]\nType=Application\n"
        f"Name={name}\nExec={exec_line}\nIcon={icon}\nTerminal=false\nCategories=Utility;\n")
    return entry


def safe_extract(path: Path, dest: Path) -> None:
    """Extract an archive, refusing entries that escape dest and links."""
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()

    def check(member_name: str) -> None:
        if not (root / member_name).resolve().is_relative_to(root):
            raise InstallError(f"Unsafe path in archive: {member_name}")

    if tarfile.is_tarfile(path):
        with tarfile.open(path) as tar:
            for m in tar.getmembers():
                check(m.name)
                if m.issym() or m.islnk():
                    raise InstallError(f"Links are not allowed in archives: {m.name}")
            tar.extractall(dest)
    else:
        with zipfile.ZipFile(path) as zf:
            for n in zf.namelist():
                check(n)
            zf.extractall(dest)


def _is_elf(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def find_flutter_executable(dest: Path) -> Path:
    """The bundle root is the folder holding data/flutter_assets; its main program is an ELF file."""
    for assets in dest.rglob("flutter_assets"):
        if assets.parent.name != "data":
            continue
        root = assets.parent.parent
        programs = [p for p in root.iterdir()
                    if p.is_file() and not p.name.endswith(".so") and _is_elf(p)]
        if programs:
            return sorted(programs, key=lambda p: p.name != root.name)[0]
    raise InstallError("No Flutter program found in this archive")


# ---------- installers ----------

def _install_flutter(path: Path, apps_dir: Path, desktop_dir: Path) -> str:
    name = path.name.split(".")[0]
    dest = apps_dir / safe_name(name)
    if dest.exists():
        shutil.rmtree(dest)
    safe_extract(path, dest)
    program = find_flutter_executable(dest)
    program.chmod(0o755)
    write_desktop_entry(name, f'"{program}"', desktop_dir)
    return f"Installed {name}. Find it in the application menu."


def _install_windows(path: Path, apps_dir: Path, desktop_dir: Path, runner: Runner) -> str:
    if not shutil.which("wine"):
        raise MissingTool("wine")
    target_dir = apps_dir / "Windows"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    shutil.copy2(path, target)
    is_msi = path.suffix.lower() == ".msi"
    cmd = ["wine", "msiexec", "/i", str(target)] if is_msi else ["wine", str(target)]
    code = runner(cmd)
    if code != 0:
        raise InstallError(f"Wine reported an error (code {code}). The app may not be compatible.")
    if not is_msi:
        write_desktop_entry(path.stem, f'wine "{target}"', desktop_dir)
    return f"Ran {path.name} with Wine."


def _install_deb(path: Path, runner: Runner) -> str:
    if runner(["pkexec", "apt-get", "install", "-y", str(path)]) != 0:
        raise InstallError("Package installation failed")
    return f"Installed {path.name}."


def _install_flatpak(path: Path, runner: Runner) -> str:
    if not shutil.which("flatpak"):
        raise MissingTool("flatpak")
    if runner(["flatpak", "install", "--user", "-y", "--noninteractive", str(path)]) != 0:
        raise InstallError("Flatpak installation failed")
    return f"Installed {path.name}."


def _install_appimage(path: Path, apps_dir: Path, desktop_dir: Path) -> str:
    apps_dir.mkdir(parents=True, exist_ok=True)
    target = apps_dir / path.name
    shutil.copy2(path, target)
    target.chmod(0o755)
    write_desktop_entry(path.stem, f'"{target}"', desktop_dir)
    return f"Installed {path.stem}. Find it in the application menu."


def install(path: Path, runner: Runner = run_command,
            apps_dir: Optional[Path] = None, desktop_dir: Optional[Path] = None) -> InstallResult:
    apps_dir = apps_dir or APPS_DIR
    desktop_dir = desktop_dir or DESKTOP_DIR
    kind = detect_kind(path)
    if kind is Kind.FLUTTER:
        message = _install_flutter(path, apps_dir, desktop_dir)
    elif kind is Kind.WINDOWS:
        message = _install_windows(path, apps_dir, desktop_dir, runner)
    elif kind is Kind.DEB:
        message = _install_deb(path, runner)
    elif kind is Kind.FLATPAK:
        message = _install_flatpak(path, runner)
    elif kind is Kind.APPIMAGE:
        message = _install_appimage(path, apps_dir, desktop_dir)
    else:
        raise InstallError("This file type is not supported")
    return InstallResult(kind, message)


def install_wine(runner: Runner = run_command) -> None:
    """Install Wine on request (it is optional and not part of the base system)."""
    if runner(["pkexec", "apt-get", "install", "-y", "wine"]) != 0:
        raise InstallError("Could not install Wine")
