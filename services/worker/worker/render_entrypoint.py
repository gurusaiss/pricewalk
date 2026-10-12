"""Entrypoint for running the arq worker as a Render free-tier "Web Service".

Render's free plan only offers Web Services, which must bind to $PORT and
answer HTTP requests or Render considers them unhealthy and recycles them.
The worker itself has no HTTP interface, so this starts a trivial health
server in a background thread (for Render's health check and for an external
uptime monitor to ping, keeping the service from spinning down) while the
real arq worker loop runs on the main thread.
"""

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from arq import run_worker

from .main import WorkerSettings


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


def _serve_health(port: int) -> None:
    HTTPServer(("0.0.0.0", port), _HealthHandler).serve_forever()


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    threading.Thread(target=_serve_health, args=(port,), daemon=True).start()
    run_worker(WorkerSettings)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
