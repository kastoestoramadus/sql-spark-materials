"""Tiny receiver for OpenLineage events: POSTs land in ol-events.jsonl (stdlib only)."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PROTO = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(PROTO, "records", "ol-events.jsonl")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "ab") as f:
            f.write(body + b"\n")
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"accepted": true}')

    def log_message(self, format: str, *args: object) -> None:
        return  # keep stdout quiet


if __name__ == "__main__":
    with open(OUT, "wb"):
        pass  # truncate previous capture
    HTTPServer(("127.0.0.1", 9500), Handler).serve_forever()
