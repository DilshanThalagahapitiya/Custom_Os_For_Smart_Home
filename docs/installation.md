# Installation

1. Download the ISO and its `.sha256` from the CI run artifacts. Verify: `sha256sum -c dilshan-os-*.iso.sha256`.
2. Write it to a USB stick (double-check the device name; this erases the stick):
   `sudo dd if=dilshan-os-*.iso of=/dev/sdX bs=4M status=progress conv=fsync`
3. Boot from the USB stick (UEFI or legacy BIOS). The live desktop starts automatically.
4. Double-click **Install** on the desktop (or use the menu). Calamares asks you to choose the disk.
   Nothing is written to disk until you confirm on the final summary page.

Live user: `user`, password `live`.
