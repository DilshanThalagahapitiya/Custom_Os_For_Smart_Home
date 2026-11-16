#!/bin/sh
# Apply the ISO's overlay files, start a virtual display, XFCE and the noVNC web server (port 6080).
cp -a /cfg/etc/xdg/. /etc/xdg/
cp -a /cfg/usr/share/. /usr/share/
cp -a /cfg/usr/bin/. /usr/bin/
Xtigervnc :1 -geometry 1280x800 -SecurityTypes None -rfbport 5901 &
sleep 3
dbus-launch --exit-with-session startxfce4 \
  >/dev/null 2>&1 &
# noVNC on 6081 (inside the iframe); boot screen + shutdown API on 6080 (PID 1)
websockify --web /usr/share/novnc 6081 localhost:5901 &
exec python3 /opt/web/os-shell.py
