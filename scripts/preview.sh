#!/usr/bin/env bash
# Start/stop the Dilshan OS desktop preview (runs in the background).
# Usage: scripts/preview.sh start | stop [--all] | status | logs
#   stop --all also stops the Linux VM (colima) to free RAM.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME=dilshan-os-preview
IMAGE=dilshan-dev-desktop
URL="http://localhost:6080"

running() { [ -n "$(docker ps -q -f "name=^${NAME}$" 2>/dev/null)" ]; }

start() {
  colima status >/dev/null 2>&1 || colima start --arch x86_64 --vm-type qemu --cpu 4 --memory 6 --disk 25
  running && { echo "Already running: $URL"; return; }
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker build -q -t "$IMAGE" -f "$ROOT/dev/Dockerfile.desktop" "$ROOT/dev" >/dev/null
  docker run -d --rm --init --name "$NAME" \
    -p 127.0.0.1:6080:6080 -p 127.0.0.1:6081:6081 -p 127.0.0.1:5901:5901 \
    -v "$ROOT/src:/app/src:ro" \
    -v "$ROOT/build/live-build/config/includes.chroot:/cfg:ro" \
    "$IMAGE" >/dev/null
  printf "Starting"
  for _ in $(seq 1 120); do
    curl -s localhost:6080/status 2>/dev/null | grep -q '"desktop": true' && break
    printf "."; sleep 3
  done
  echo
  echo "Browser: $URL"
  echo "VNC app: vnc://localhost:5901 (password: dilshan)"
  command -v open >/dev/null && open "$URL" || true
}

stop() {
  docker rm -f "$NAME" >/dev/null 2>&1 && echo "Preview stopped." || echo "Preview was not running."
  if [ "${1:-}" = "--all" ]; then colima stop && echo "VM stopped."; fi
}

case "${1:-}" in
  start)  start ;;
  stop)   stop "${2:-}" ;;
  status) running && echo "Running: $URL" || echo "Stopped" ;;
  logs)   docker logs -f "$NAME" ;;
  *) echo "Usage: $0 start | stop [--all] | status | logs" >&2; exit 1 ;;
esac
