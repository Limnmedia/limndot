"""GUI-independent render request sequencing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenderRequest:
    """An immutable snapshot of one render request."""

    request_id: int
    dot_source: str
    engine: str


class RenderRequestController:
    """Assign request IDs and reject results superseded by newer input."""

    def __init__(self) -> None:
        self._current_request_id = 0

    @property
    def current_request_id(self) -> int:
        return self._current_request_id

    def issue(self, dot_source: str, engine: str) -> RenderRequest:
        self._current_request_id += 1
        return RenderRequest(self._current_request_id, dot_source, engine)

    def is_current(self, request_id: int) -> bool:
        return request_id == self._current_request_id
