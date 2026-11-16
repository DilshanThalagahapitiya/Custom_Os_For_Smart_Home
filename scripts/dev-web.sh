#!/usr/bin/env bash
# Preview a Dilshan OS GTK app in your browser without building an ISO.
# Usage: scripts/dev-web.sh [memory_monitor|power_settings]   then open http://localhost:8085
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:-memory_monitor}"
docker build -q -t dilshan-dev "$ROOT/dev" >/dev/null
echo "Open http://localhost:8085  (close the app window to reload your latest code; Ctrl+C to stop)"
docker run --rm -p 8085:8085 -v "$ROOT/src:/app/src:ro" dilshan-dev "$APP"
