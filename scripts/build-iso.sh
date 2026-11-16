#!/usr/bin/env bash
# Build the Dilshan OS live ISO. Needs root on Debian 12 (use scripts/build-in-docker.sh elsewhere).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
WORK="${WORK_DIR:-$ROOT/build/work}"
OUT="${OUT_DIR:-$ROOT/dist}"
ISO_NAME="dilshan-os-${VERSION}-amd64.iso"

[ "$(id -u)" -eq 0 ] || { echo "Run as root (or via scripts/build-in-docker.sh)" >&2; exit 1; }

install_deps() {
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    live-build debootstrap xorriso squashfs-tools mtools dosfstools \
    grub-pc-bin grub-efi-amd64-bin grub-common ca-certificates gnupg \
    debian-archive-keyring git
}
command -v lb >/dev/null || install_deps

# Reproducible timestamps: last commit time, else a fixed date
SOURCE_DATE_EPOCH="$(git -C "$ROOT" log -1 --format=%ct 2>/dev/null || echo 1700000000)"
export SOURCE_DATE_EPOCH

rm -rf "$WORK" && mkdir -p "$WORK" "$OUT"
cp -a "$ROOT/build/live-build/." "$WORK/"
mkdir -p "$WORK/config/includes.chroot/usr/lib"
sed "s/@VERSION@/${VERSION}/g" "$ROOT/branding/os-release.in" \
  > "$WORK/config/includes.chroot/usr/lib/os-release"

cd "$WORK"
lb config \
  --mode debian \
  --distribution bookworm \
  --architectures amd64 \
  --linux-flavours amd64 \
  --archive-areas "main contrib non-free-firmware" \
  --binary-images iso-hybrid \
  --bootloaders "grub-pc,grub-efi" \
  --debian-installer none \
  --apt-recommends false \
  --memtest none \
  --iso-application "Dilshan OS" \
  --iso-volume "DILSHAN_OS" \
  --iso-publisher "Dilshan OS project" \
  --bootappend-live "boot=live components quiet hostname=dilshan-os locales=en_US.UTF-8 keyboard-layouts=us"
lb build

ISO="$(ls "$WORK"/*.iso | head -n1)"
mv "$ISO" "$OUT/$ISO_NAME"
(cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256")
echo "Built: $OUT/$ISO_NAME ($(du -h "$OUT/$ISO_NAME" | cut -f1))"
