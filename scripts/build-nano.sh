#!/usr/bin/env bash
# Build the tiny Dilshan OS Nano ISO (Alpine x86 kernel + BusyBox rootfs, ~10-15 MB).
# Only assembles files, so it is fast even on an emulated or non-x86 host.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
WORK="${WORK_DIR:-/var/tmp/dilshan-nano}"
OUT="${OUT_DIR:-$ROOT/dist}"
MIRROR="https://dl-cdn.alpinelinux.org/alpine/latest-stable"
ISO_NAME="dilshan-os-nano-${VERSION}-i386.iso"

command -v xorriso >/dev/null || {
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl ca-certificates xorriso isolinux syslinux-common cpio gzip
}

rm -rf "$WORK" && mkdir -p "$WORK"/{rootfs,iso/boot,iso/isolinux} "$OUT"
cd "$WORK"

# Find current Alpine file names
ROOTFS_FILE="$(curl -fsSL "$MIRROR/releases/x86/latest-releases.yaml" \
  | grep -m1 -o 'alpine-minirootfs-[0-9.]*-x86.tar.gz')"
KERNEL_VER="$(curl -fsSL "$MIRROR/main/x86/APKINDEX.tar.gz" | tar -xzO APKINDEX \
  | awk 'BEGIN{RS="";FS="\n"} {f=0; for(i=1;i<=NF;i++){ if($i=="P:linux-virt")f=1; if(f&&!d&&$i ~ /^V:/){print substr($i,3); d=1} }}')"
[ -n "$ROOTFS_FILE" ] && [ -n "$KERNEL_VER" ] || { echo "Could not resolve Alpine files" >&2; exit 1; }
echo "Using $ROOTFS_FILE and linux-virt $KERNEL_VER"

curl -fsSL -o rootfs.tar.gz "$MIRROR/releases/x86/$ROOTFS_FILE"
curl -fsSL -o kernel.apk "$MIRROR/main/x86/linux-virt-${KERNEL_VER}.apk"

# Kernel
mkdir kernel && tar -xzf kernel.apk -C kernel boot/vmlinuz-virt 2>/dev/null || true
[ -f kernel/boot/vmlinuz-virt ] || { echo "Kernel not found in apk" >&2; exit 1; }
cp kernel/boot/vmlinuz-virt iso/boot/vmlinuz

# Root filesystem: Alpine minirootfs + our overlay
tar -xzf rootfs.tar.gz -C rootfs
cp -a "$ROOT/build/nano/rootfs/." rootfs/
sed "s/@VERSION@/${VERSION}/g" "$ROOT/build/nano/os-release.in" > rootfs/etc/os-release
ln -sf sbin/init rootfs/init
(cd rootfs && find . | cpio -o -H newc --owner 0:0 2>/dev/null | gzip -9) > iso/boot/initrd.gz

# BIOS boot files
cp /usr/lib/ISOLINUX/isolinux.bin /usr/lib/syslinux/modules/bios/ldlinux.c32 iso/isolinux/
cp "$ROOT/build/nano/isolinux.cfg" iso/isolinux/

xorriso -as mkisofs -quiet -o "$OUT/$ISO_NAME" -V DILSHAN_NANO \
  -b isolinux/isolinux.bin -c isolinux/boot.cat \
  -no-emul-boot -boot-load-size 4 -boot-info-table iso
(cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256")
echo "Built: $OUT/$ISO_NAME ($(du -h "$OUT/$ISO_NAME" | cut -f1))"
