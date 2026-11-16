#!/usr/bin/env bash
# Boot an ISO in QEMU and wait for the guest to report DILSHAN_BOOT_OK on the serial port.
# Usage: tests/boot-test.sh <iso> <bios|uefi> [ram_mb] [cpus] [timeout_s]
set -euo pipefail

ISO="${1:?iso path}"; MODE="${2:?bios|uefi}"
RAM="${3:-2048}"; CPUS="${4:-2}"; TIMEOUT="${5:-900}"
OUT="${OUT_DIR:-test-output}"; mkdir -p "$OUT"
SERIAL="$OUT/serial-$MODE-${RAM}m.log"; SHOT="$OUT/screen-$MODE-${RAM}m.ppm"
MON="$(mktemp -u)"; : > "$SERIAL"

args=(-m "$RAM" -smp "$CPUS" -cdrom "$ISO" -boot d -vga std -display none
      -serial "file:$SERIAL" -monitor "unix:$MON,server,nowait" -no-reboot)

if [ -w /dev/kvm ]; then args+=(-enable-kvm -cpu host); else args+=(-cpu max); fi

if [ "$MODE" = uefi ]; then
  FW="$(find /usr/share/ovmf /usr/share/OVMF -name OVMF.fd 2>/dev/null | head -n1)"
  [ -n "$FW" ] || { echo "OVMF firmware not found" >&2; exit 2; }
  args+=(-bios "$FW")
fi

qemu-system-x86_64 "${args[@]}" &
QPID=$!
trap 'kill $QPID 2>/dev/null || true' EXIT

for ((t = 0; t < TIMEOUT; t += 5)); do
  if grep -q DILSHAN_BOOT_OK "$SERIAL"; then
    sleep 3
    grep -q zram0 "$SERIAL" || { echo "FAIL: zram swap not active" >&2; cat "$SERIAL" >&2; exit 1; }
    cat "$SERIAL"
    echo "PASS: $MODE ${RAM}MB booted to graphical.target in ~${t}s"
    echo "screendump $SHOT" | socat - "UNIX-CONNECT:$MON" >/dev/null 2>&1 || true
    sleep 1; exit 0
  fi
  kill -0 $QPID 2>/dev/null || { echo "FAIL: QEMU exited early" >&2; exit 1; }
  sleep 5
done
echo "FAIL: no boot marker within ${TIMEOUT}s ($MODE ${RAM}MB)" >&2
echo "screendump $SHOT" | socat - "UNIX-CONNECT:$MON" >/dev/null 2>&1 || true
exit 1
