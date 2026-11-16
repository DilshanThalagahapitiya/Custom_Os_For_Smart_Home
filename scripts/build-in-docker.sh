#!/usr/bin/env bash
# Build the ISO inside a Debian 12 container (any host with Docker, x86-64 recommended).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm --privileged -v "$ROOT:/src" -w /src debian:bookworm ./scripts/build-iso.sh
