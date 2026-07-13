"""Static registry for LIMNDOT's built-in adapters."""

from __future__ import annotations

from pathlib import Path

from .base import GraphAdapter
from .graph_json import JsonGraphAdapter
from .relationships_csv import CsvRelationshipAdapter


class AdapterRegistry:
    def __init__(self, adapters: list[GraphAdapter] | None = None) -> None:
        builtins: list[GraphAdapter] = [CsvRelationshipAdapter(), JsonGraphAdapter()]
        self._adapters = {adapter.name: adapter for adapter in (adapters or builtins)}

    def available(self) -> tuple[GraphAdapter, ...]:
        return tuple(self._adapters[name] for name in sorted(self._adapters))

    def get(self, name: str) -> GraphAdapter | None:
        return self._adapters.get(name)

    def resolve(self, path: Path | str | None, explicit_name: str | None = None) -> GraphAdapter | None:
        if explicit_name:
            return self.get(explicit_name)
        candidate = Path(path) if path is not None else None
        for adapter in self.available():
            if candidate and candidate.suffix.lower() in adapter.supported_extensions:
                return adapter
        return None
