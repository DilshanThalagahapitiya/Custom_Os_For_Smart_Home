#!/bin/sh
# Usage: run-app <module name in dilshan.apps>   (e.g. memory_monitor)
# Serves the app on port 8085. When the window is closed the app restarts with the latest code.
broadwayd --address 0.0.0.0 --port 8085 :5 &
sleep 3
while true; do
  python3 -c "from dilshan.apps.$1 import main; main()" || sleep 2
  sleep 0.5
done
