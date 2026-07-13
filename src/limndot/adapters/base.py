"""Adapter contract shared by built-in structured-data translators."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..graph_model import GraphDocument

MAX_NODES = 10_000
MAX_EDGES = 25_000
MAX_SOURCE_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class AdapterRequest:
    source_path: Path | None
    source_text: str
    options: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AdapterMessage:
    level: str
    message: str
    row: int | None = None
    field: str | None = None

    def display_text(self) -> str:
        location = f" row {self.row}" if self.row is not None else ""
        field = f" ({self.field})" if self.field else ""
        return f"Import {self.level.title()}{location}{field}: {self.message}"


@dataclass(slots=True)
class AdapterResult:
    success: bool
    graph: GraphDocument | None
    generated_dot: str
    messages: list[AdapterMessage]
    source_description: str
    adapter_name: str


class GraphAdapter(Protocol):
    name: str
    supported_extensions: tuple[str, ...]

    def can_handle(self, path: Path | None, source_text: str) -> bool: ...
    def generate(self, request: AdapterRequest) -> AdapterResult: ...
