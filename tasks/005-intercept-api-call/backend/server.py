"""Bundled mock backend for task 005.

A dependency-free HTTP server (stdlib only) that accepts the Pulse app's
telemetry POST so the request completes cleanly while mitmproxy records it. The
runner starts this during the interaction window and stops it afterwards.

    python server.py            # listens on 0.0.0.0:8090 (override with PORT)
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("MOCK_BACKEND_PORT", "8090"))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - stdlib naming
        length = int(self.headers.get("Content-Length", 0) or 0)
        _ = self.rfile.read(length)  # drain the body
        payload = json.dumps({"status": "accepted"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args) -> None:  # silence default stderr logging
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[mock-backend] listening on :{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
