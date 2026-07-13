"""Built-in CSV edge-list adapter."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from ..dot_serializer import serialize_dot
from ..graph_model import GraphDocument, GraphEdge, GraphNode
from .base import AdapterMessage, AdapterRequest, AdapterResult, MAX_EDGES, MAX_NODES


class CsvRelationshipAdapter:
    name = "CSV Relationships"
    supported_extensions = (".csv",)
    required_fields = {"source", "target"}
    optional_fields = {"source_label", "target_label", "label", "source_group", "target_group", "source_kind", "target_kind"}

    def can_handle(self, path: Path | None, source_text: str) -> bool:
        return bool(path and path.suffix.lower() in self.supported_extensions)

    def generate(self, request: AdapterRequest) -> AdapterResult:
        description = str(request.source_path) if request.source_path else "CSV relationship data"
        messages: list[AdapterMessage] = []
        text = request.source_text.lstrip("\ufeff")
        if not text.strip():
            return self._failure(description, [AdapterMessage("error", "CSV source is empty.")])
        try:
            reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
            headers = [header.strip() if header else "" for header in (reader.fieldnames or [])]
            reader.fieldnames = headers
            missing = sorted(self.required_fields - set(headers))
            if missing:
                return self._failure(description, [AdapterMessage("error", f"Missing required columns: {', '.join(missing)}.")])
            for field in sorted(set(headers) - self.required_fields - self.optional_fields):
                messages.append(AdapterMessage("warning", f"Unexpected column '{field}' was ignored.", field=field))

            nodes: dict[str, GraphNode] = {}
            edges: dict[tuple[str, str, str], GraphEdge] = {}
            for row_number, raw in enumerate(reader, start=2):
                if None in raw:
                    messages.append(AdapterMessage("warning", "Malformed row has more values than headers; row skipped.", row=row_number))
                    continue
                row = {str(key).strip(): (value or "").strip() for key, value in raw.items()}
                if not any(row.values()):
                    continue
                source, target = row.get("source", ""), row.get("target", "")
                if not source or not target:
                    field = "source" if not source else "target"
                    messages.append(AdapterMessage("warning", f"{field} is empty; row skipped.", row=row_number, field=field))
                    continue
                self._merge_node(nodes, source, row.get("source_label") or source, row.get("source_group") or None, row.get("source_kind") or None, row_number, messages)
                self._merge_node(nodes, target, row.get("target_label") or target, row.get("target_group") or None, row.get("target_kind") or None, row_number, messages)
                if len(nodes) > MAX_NODES:
                    return self._failure(description, messages + [AdapterMessage("error", f"Node limit of {MAX_NODES} exceeded.")])
                edge = GraphEdge(source, target, row.get("label") or None)
                key = (source, target, edge.label or "")
                if key in edges:
                    messages.append(AdapterMessage("warning", "Duplicate edge collapsed.", row=row_number))
                else:
                    edges[key] = edge
                if len(edges) > MAX_EDGES:
                    return self._failure(description, messages + [AdapterMessage("error", f"Edge limit of {MAX_EDGES} exceeded.")])
        except csv.Error as error:
            return self._failure(description, messages + [AdapterMessage("error", f"Malformed CSV: {error}.")])

        if not nodes:
            return self._failure(description, messages + [AdapterMessage("error", "CSV contains no usable relationships.")])
        name = request.source_path.stem if request.source_path else "Relationships"
        graph = GraphDocument(name=name, nodes=list(nodes.values()), edges=list(edges.values()))
        return AdapterResult(True, graph, serialize_dot(graph), messages, description, self.name)

    def _merge_node(self, nodes: dict[str, GraphNode], identifier: str, label: str, group: str | None, kind: str | None, row: int, messages: list[AdapterMessage]) -> None:
        candidate = GraphNode(identifier, label, kind, group)
        existing = nodes.get(identifier)
        if existing is None:
            nodes[identifier] = candidate
            return
        for field in ("label", "group", "kind"):
            old, new = getattr(existing, field), getattr(candidate, field)
            if new and old != new:
                messages.append(AdapterMessage("warning", f"Node '{identifier}' has conflicting {field}; first value retained.", row=row, field=field))

    def _failure(self, description: str, messages: list[AdapterMessage]) -> AdapterResult:
        return AdapterResult(False, None, "", messages, description, self.name)
