#!/usr/bin/env bash
# Build the tiny Dilshan OS Nano ISO (Alpine x86 kernel + BusyBox rootfs).
#   PROFILE=nano      text only, ~12 MB
#   PROFILE=nano-gui  Xorg + JWM light desktop (needs an x86-64 host: it runs Alpine's static apk)
# Only assembles files, so it is fast even on an emulated or non-x86 host.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
WORK="${WORK_DIR:-/var/tmp/dilshan-nano}"
OUT="${OUT_DIR:-$ROOT/dist}"
MIRROR="https://dl-cdn.alpinelinux.org/alpine/latest-stable"
PROFILE="${PROFILE:-nano}"
GUI=0; [ "$PROFILE" = nano-gui ] && GUI=1
ISO_NAME="dilshan-os-${PROFILE}-${VERSION}-i386.iso"
GUI_PACKAGES=(xorg-server xinit xf86-video-vesa xf86-video-fbdev xf86-input-libinput eudev jwm xterm font-dejavu)

command -v xorriso >/dev/null || {
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl ca-certificates xorriso isolinux syslinux-common cpio gzip
}

rm -rf "$WORK" && mkdir -p "$WORK"/{rootfs,iso/boot,iso/isolinux} "$OUT"
cd "$WORK"

# Version of an Alpine package: apk_version <arch> <package>
apk_version() {
  curl -fsSL "$MIRROR/main/$1/APKINDEX.tar.gz" | tar -xzO APKINDEX \
    | awk -v pkg="P:$2" 'BEGIN{RS="";FS="\n"} {f=0; for(i=1;i<=NF;i++){ if($i==pkg)f=1; if(f&&!d&&$i ~ /^V:/){print substr($i,3); d=1} }}'
}

# Find current Alpine file names
ROOTFS_FILE="$(curl -fsSL "$MIRROR/releases/x86/latest-releases.yaml" \
  | grep -m1 -o 'alpine-minirootfs-[0-9.]*-x86.tar.gz')"
KERNEL_VER="$(apk_version x86 linux-virt)"
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
if [ "$GUI" = 1 ]; then
  # Kernel modules (input, graphics) for udev, minus what a small desktop never needs
  tar -xzf kernel.apk -C rootfs lib/modules 2>/dev/null || true
  rm -rf rootfs/lib/modules/*/kernel/{sound,net,drivers/net,drivers/media,drivers/bluetooth,drivers/infiniband,drivers/scsi,fs/ocfs2,fs/btrfs}
  # Install X and the window manager with Alpine's static apk (needs an x86-64 host)
  APK_TOOLS="$(apk_version x86_64 apk-tools-static)"
  curl -fsSL -o apk-tools.apk "$MIRROR/main/x86_64/apk-tools-static-${APK_TOOLS}.apk"
  mkdir apk && tar -xzf apk-tools.apk -C apk sbin/apk.static 2>/dev/null || true
  ./apk/sbin/apk.static -X "$MIRROR/main" -X "$MIRROR/community" --root rootfs --arch x86 \
    --no-scripts --no-cache --allow-untrusted add "${GUI_PACKAGES[@]}"
  cp -a "$ROOT/build/nano/gui/." rootfs/
  # Software-rendering stack (LLVM, Gallium) is ~240 MB and unused by the vesa/fbdev drivers
  rm -rf rootfs/usr/lib/libLLVM* rootfs/usr/lib/libgallium* rootfs/usr/lib/dri rootfs/usr/lib/gbm
  rm -rf rootfs/usr/share/{doc,man,locale} rootfs/var/cache/apk/*
fi
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
