from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

Handler = Callable[[], dict[str, str]]


@dataclass
class Response:
    status_code: int
    _json: dict[str, str]

    def json(self) -> dict[str, str]:
        return self._json


class FastAPI:
    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], Handler] = {}

    def get(self, path: str) -> Callable[[Handler], Handler]:
        def decorator(func: Handler) -> Handler:
            self._routes[("GET", path)] = func
            return func

        return decorator

    def _handle(self, method: str, path: str) -> Response:
        handler = self._routes.get((method, path))
        if handler is None:
            return Response(status_code=404, _json={"detail": "Not Found"})
        return Response(status_code=200, _json=handler())
