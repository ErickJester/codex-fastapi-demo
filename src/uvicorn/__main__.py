from __future__ import annotations

import argparse
import importlib
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from fastapi import FastAPI


class RequestHandler(BaseHTTPRequestHandler):
    app: FastAPI

    def do_GET(self) -> None:  # noqa: N802
        response = self.app._handle("GET", self.path)
        payload = json.dumps(response.json()).encode("utf-8")
        self.send_response(response.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:
        return


def _load_app(app_path: str) -> FastAPI:
    module_path, app_name = app_path.split(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, app_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal uvicorn shim")
    parser.add_argument("app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    app = _load_app(args.app)
    RequestHandler.app = app

    server = HTTPServer((args.host, args.port), RequestHandler)
    print(f"Serving on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
