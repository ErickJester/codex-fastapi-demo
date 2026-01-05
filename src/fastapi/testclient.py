from __future__ import annotations

from fastapi import FastAPI


class TestClient:
    __test__ = False

    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def get(self, path: str):
        return self._app._handle("GET", path)
