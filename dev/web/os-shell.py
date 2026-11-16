"""Preview shell: boot screen, status, and shutdown for the browser desktop preview (port 6080)."""
import json
import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB = Path(__file__).parent
UPLOADS = Path("/root/Uploads")


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def desktop_ready() -> bool:
    return subprocess.run(["pgrep", "-x", "xfce4-panel"], capture_output=True).returncode == 0


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, kind: str = "text/html", code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            state = {"display": port_open(5901), "desktop": desktop_ready()}
            self._send(json.dumps(state).encode(), "application/json")
        else:
            self._send((WEB / "index.html").read_bytes())

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/upload":
            return self._upload(parse_qs(url.query).get("name", ["file"])[0])
        if url.path != "/shutdown":
            return self._send(b"not found", "text/plain", 404)
        self._send(b"{}", "application/json")
        # Close the session cleanly, then end the container (this process is PID 1)
        subprocess.run(["xfce4-session-logout", "--logout"], capture_output=True, timeout=5)
        threading.Timer(2.0, lambda: os._exit(0)).start()

    def _upload(self, name: str) -> None:
        """Save an uploaded file to ~/Uploads inside the preview so App Installer can use it."""
        UPLOADS.mkdir(parents=True, exist_ok=True)
        target = UPLOADS / (Path(name).name or "file")
        remaining = int(self.headers.get("Content-Length", 0))
        with target.open("wb") as out:
            while remaining > 0:
                chunk = self.rfile.read(min(1 << 20, remaining))
                if not chunk:
                    break
                out.write(chunk)
                remaining -= len(chunk)
        self._send(json.dumps({"saved": target.name}).encode(), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 6080), Handler).serve_forever()
