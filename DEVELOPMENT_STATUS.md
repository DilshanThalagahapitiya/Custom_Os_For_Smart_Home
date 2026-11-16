# Development Status

## Phase 1: Bootable foundation
### Written, NOT yet verified (first CI run pending)
- live-build configuration (Debian 12, XFCE, LightDM, Calamares, GRUB BIOS+UEFI)
- Basic theme, wallpaper, OS name in `os-release`/issue/installer text
- GitHub Actions: lint → build ISO → QEMU boot test (BIOS, UEFI, 2 GB RAM, 2 CPUs)

### Verified
Nothing yet. No ISO has been built or booted.

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

## Latest successful ISO build
None.

## Latest test results
None.
