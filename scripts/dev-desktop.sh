#!/usr/bin/env bash
# Preview the whole Dilshan OS desktop in your browser, without building an ISO.
# Open http://localhost:6080
# Config comes live from build/live-build/config/includes.chroot; restart the script to apply changes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker build -q -t dilshan-dev-desktop -f "$ROOT/dev/Dockerfile.desktop" "$ROOT/dev" >/dev/null
echo "Open http://localhost:6080  (Ctrl+C to stop)"
docker run --rm --init -p 127.0.0.1:6080:6080 -p 127.0.0.1:6081:6081 \
  -v "$ROOT/src:/app/src:ro" \
  -v "$ROOT/build/live-build/config/includes.chroot:/cfg:ro" \
  dilshan-dev-desktop
