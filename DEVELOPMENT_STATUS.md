# Development Status

## Phase 1: Bootable foundation
### Written, NOT yet verified (first CI run pending)
- live-build configuration (Debian 12, XFCE, LightDM, Calamares, GRUB BIOS+UEFI)
- Basic theme, wallpaper, OS name in `os-release`/issue/installer text
- GitHub Actions: lint → build ISO → QEMU boot test (BIOS, UEFI, 2 GB RAM, 2 CPUs)

## Phase 2: Performance (written, NOT verified)
- zram swap, sysctl tuning, earlyoom, power-profiles-daemon, wait-online masked
- Memory Monitor and Power Settings GTK apps (`src/dilshan`)
- Boot test now also requires zram swap to be active
- Not done yet: optional disk swap, memory-leak monitoring, thermal/fan display, hibernate, measured targets

### Verified
- 10 Python unit tests for memory/power parsing pass locally (`tests/unit`).
- ISO build and VM boot: nothing yet. No ISO has been built or booted.

### Known issues / risks
- Installer shortcut is copied to `/etc/skel/Desktop`, so installed users also get it.
- Calamares config is Debian's default, only text-rebranded; a custom config is pending.
- Installation to disk is not yet tested in a VM.
- `grub-pc` bootloader mode of live-build is less common than syslinux; fall back to syslinux if the BIOS boot fails.

### Pending
- Fix whatever the first CI run reveals
- Automated install test (install in QEMU, reboot, check boot)
- Measure ISO size, idle RAM and boot time
- 4 GB / 8 GB and single-core boot tests

## Nano images (side project for small/browser testing)
- `PROFILE=nano` (12 MB, text) and `PROFILE=nano-gui` (54 MB, Xorg + JWM) built locally and booted in QEMU i386; nano-gui reaches the desktop. Not tested in v86.

## Latest successful ISO build
None.

## Latest test results
None.
