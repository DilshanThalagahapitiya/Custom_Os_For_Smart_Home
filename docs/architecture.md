# Architecture (Phase 1)

| Layer | Choice |
|---|---|
| Base | Debian 12 bookworm, amd64 |
| Kernel | Debian `linux-image-amd64` (6.1 LTS), no custom build |
| Boot | GRUB: `grub-pc` (BIOS) + `grub-efi` (UEFI), hybrid ISO |
| Init | systemd |
| Desktop | XFCE on X11, LightDM, Arc-Dark / Papirus-Dark / Inter, compositing off |
| Installer | Calamares (`calamares-settings-debian`, rebranded in a build hook) |
| Build | `live-build`, run in a Debian 12 container |

## Design rules
- Keep the system `ID=debian` so APT and packages stay compatible; only display names change.
- Image content lives in `build/live-build/config/` as plain package lists, files and hooks. No logic is duplicated in scripts.
- `apt-recommends=false` keeps the image small; needed extras are listed explicitly.
- Bootloader packages for both BIOS and UEFI are in the image so the installer can target either.

## Build dependencies
`live-build debootstrap xorriso squashfs-tools mtools dosfstools grub-pc-bin grub-efi-amd64-bin` (installed automatically by `scripts/build-iso.sh`).

## Size/RAM
Targets only, to be measured: ISO ~1–1.3 GB, idle RAM ~350–500 MB, minimum 2 GB RAM / 16 GB disk.

## Roadmap
Phases 2–7 as in the project brief: performance, GUI apps, recovery, software centre, smart home, release.
