#!/usr/bin/env bash
# Build the Dilshan OS live ISO. Needs root on Debian 12 (use scripts/build-in-docker.sh elsewhere).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
WORK="${WORK_DIR:-$ROOT/build/work}"
OUT="${OUT_DIR:-$ROOT/dist}"
# PROFILE=desktop (default): 64-bit XFCE desktop. PROFILE=lite: 32-bit console image for browser emulators.
PROFILE="${PROFILE:-desktop}"
case "$PROFILE" in
  desktop)
    CONFIG_DIR="$ROOT/build/live-build"; ARCH=amd64; FLAVOUR=amd64; BOOTLOADERS="grub-pc,grub-efi"
    APPEND="boot=live components quiet hostname=dilshan-os locales=en_US.UTF-8 keyboard-layouts=us" ;;
  lite)
    CONFIG_DIR="$ROOT/build/live-build-lite"; ARCH=i386; FLAVOUR=686; BOOTLOADERS="syslinux"
    APPEND="boot=live components hostname=dilshan-lite locales=en_US.UTF-8 keyboard-layouts=us" ;;
  *) echo "Unknown PROFILE '$PROFILE' (desktop|lite)" >&2; exit 1 ;;
esac
ISO_NAME="dilshan-os-${PROFILE}-${VERSION}-${ARCH}.iso"

[ "$(id -u)" -eq 0 ] || { echo "Run as root (or via scripts/build-in-docker.sh)" >&2; exit 1; }

install_deps() {
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    live-build debootstrap xorriso squashfs-tools mtools dosfstools \
    grub-pc-bin grub-efi-amd64-bin grub-common ca-certificates gnupg \
    debian-archive-keyring git syslinux syslinux-common isolinux
}
command -v lb >/dev/null || install_deps

# Reproducible timestamps: last commit time, else a fixed date
SOURCE_DATE_EPOCH="$(git -C "$ROOT" log -1 --format=%ct 2>/dev/null || echo 1700000000)"
export SOURCE_DATE_EPOCH

rm -rf "$WORK" && mkdir -p "$WORK" "$OUT"
cp -a "$CONFIG_DIR/." "$WORK/"
mkdir -p "$WORK/config/includes.chroot/usr/lib"
sed "s/@VERSION@/${VERSION}/g" "$ROOT/branding/os-release.in" \
  > "$WORK/config/includes.chroot/usr/lib/os-release"

# Python tools go to the system site-packages (desktop only)
[ "$PROFILE" = desktop ] && {
PYDEST="$WORK/config/includes.chroot/usr/lib/python3/dist-packages"
mkdir -p "$PYDEST"
cp -a "$ROOT/src/dilshan" "$PYDEST/"
find "$PYDEST" -name __pycache__ -prune -exec rm -rf {} +
}

# FAST=1: gzip squashfs. Builds much sooner, ISO is larger. Use for test builds.
COMPRESSION="xz"; [ "${FAST:-0}" = 1 ] && COMPRESSION="gzip"

cd "$WORK"
lb config \
  --mode debian \
  --distribution bookworm \
  --architectures "$ARCH" \
  --linux-flavours "$FLAVOUR" \
  --archive-areas "main contrib non-free-firmware" \
  --binary-images iso-hybrid \
  --bootloaders "$BOOTLOADERS" \
  --debian-installer none \
  --chroot-squashfs-compression-type "$COMPRESSION" \
  --apt-recommends false \
  --memtest none \
  --iso-application "Dilshan OS" \
  --iso-volume "DILSHAN_OS" \
  --iso-publisher "Dilshan OS project" \
  --bootappend-live "$APPEND"
lb build

ISO="$(find "$WORK" -maxdepth 1 -name '*.iso' | head -n1)"
mv "$ISO" "$OUT/$ISO_NAME"
(cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256")
echo "Built: $OUT/$ISO_NAME ($(du -h "$OUT/$ISO_NAME" | cut -f1))"
