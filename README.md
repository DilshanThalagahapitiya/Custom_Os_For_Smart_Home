# Dilshan OS

A lightweight, installable Debian-based Linux distribution for old computers and smart-home servers.

**Status: Phase 1 (bootable foundation), pre-release. See [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) for what is actually verified.**

## Stack
Debian 12 (bookworm) · Linux 6.1 LTS (Debian kernel) · GRUB (BIOS + UEFI) · systemd · XFCE + LightDM (X11) · Calamares installer · built with Debian `live-build`.

## Build
- **CI (recommended):** push to GitHub. The workflow builds the ISO, then boots it in QEMU (BIOS and UEFI). Download the ISO from the run's artifacts.
- **Locally (Docker, x86-64 host):** `./scripts/build-in-docker.sh` → `dist/dilshan-os-<version>-amd64.iso` + `.sha256`
- **On Debian 12 as root:** `./scripts/build-iso.sh`

## Preview the desktop (no ISO)
Double-click `start-os.command` (or `./scripts/preview.sh start`). It opens http://localhost:6080; VNC: `vnc://localhost:5901`, password `dilshan`.
Stop with `stop-os.command` (or `./scripts/preview.sh stop --all`). Also: `status`, `logs`.

## Develop without building an ISO
`./scripts/dev-web.sh memory_monitor` (or `power_settings`) runs the GTK app in a container and shows it at http://localhost:8085. Your `src/` folder is mounted live: edit, close the app window, and it reloads. Needs Docker (colima) running.

## Test
`tests/boot-test.sh dist/*.iso bios|uefi 2048 2` boots the ISO in QEMU and waits for the guest to report it reached the graphical target.

## Layout
| Path | Purpose |
|---|---|
| `build/live-build/config/` | package lists, hooks, files copied into the image |
| `branding/` | templates for OS identity |
| `scripts/` | build entry points |
| `tests/` | VM boot tests |
| `docs/` | architecture and installation |

Licensed under GPL-3.0.
