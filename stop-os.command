#!/bin/bash
cd "$(dirname "$0")" && ./scripts/preview.sh stop --all
echo; read -n 1 -s -r -p "Press any key to close"
