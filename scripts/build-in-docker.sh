#!/usr/bin/env bash
# Build the ISO inside a Debian 12 container (any host with Docker, x86-64 recommended).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT=./scripts/build-iso.sh
[ "${PROFILE:-}" = nano ] && SCRIPT=./scripts/build-nano.sh
docker run --rm --privileged -e FAST -e PROFILE -e WORK_DIR=/var/tmp/dilshan-work -v "$ROOT:/src" -w /src debian:bookworm "$SCRIPT"
