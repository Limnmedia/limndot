"""Built-in explicit JSON graph adapter."""

from __future__ import annotations

import json
from pathlib import Path

from ..dot_serializer import ATTRIBUTE_NAME, serialize_dot
from ..graph_model import GraphDocument, GraphEdge, GraphNode
from .base import AdapterMessage, AdapterRequest, AdapterResult, MAX_EDGES, MAX_NODES


class JsonGraphAdapter:
    name = "JSON Graph"
    supported_extensions = (".json",)
    top_fields = {"name", "directed", "graph_attributes", "node_attributes", "edge_attributes", "nodes", "edges"}
    node_fields = {"id", "label", "group", "kind", "attributes"}
    edge_fields = {"source", "target", "label", "kind", "attributes"}

    def can_handle(self, path: Path | None, source_text: str) -> bool:
        return bool(path and path.suffix.lower() in self.supported_extensions)

    def generate(self, request: AdapterRequest) -> AdapterResult:
        description = str(request.source_path) if request.source_path else "JSON graph data"
        messages: list[AdapterMessage] = []
        try:
            data = json.loads(request.source_text.lstrip("\ufeff"))
        except json.JSONDecodeError as error:
            return self._failure(description, [AdapterMessage("error", f"Malformed JSON at line {error.lineno}, column {error.colno}: {error.msg}.")])
        if not isinstance(data, dict):
            return self._failure(description, [AdapterMessage("error", "Top-level JSON value must be an object.")])
        for field in sorted(set(data) - self.top_fields):
            messages.append(AdapterMessage("warning", f"Unsupported top-level field '{field}' was ignored.", field=field))
        raw_nodes, raw_edges = data.get("nodes", []), data.get("edges", [])
        if not isinstance(raw_nodes, list):
            return self._failure(description, messages + [AdapterMessage("error", "'nodes' must be a list.", field="nodes")])
        if not isinstance(raw_edges, list):
            return self._failure(description, messages + [AdapterMessage("error", "'edges' must be a list.", field="edges")])
        if len(raw_nodes) > MAX_NODES:
            return self._failure(description, messages + [AdapterMessage("error", f"Node limit of {MAX_NODES} exceeded.")])
        if len(raw_edges) > MAX_EDGES:
            return self._failure(description, messages + [AdapterMessage("error", f"Edge limit of {MAX_EDGES} exceeded.")])

        nodes: list[GraphNode] = []
        node_ids: set[str] = set()
        fatal = False
        for index, raw in enumerate(raw_nodes, start=1):
            if not isinstance(raw, dict):
                messages.append(AdapterMessage("error", "Node must be an object.", row=index)); fatal = True; continue
            for field in sorted(set(raw) - self.node_fields):
                messages.append(AdapterMessage("warning", f"Unsupported node field '{field}' was ignored.", row=index, field=field))
            identifier = self._text(raw.get("id"))
            if not identifier:
                messages.append(AdapterMessage("error", "Node ID must be nonempty.", row=index, field="id")); fatal = True; continue
            if identifier in node_ids:
                messages.append(AdapterMessage("error", f"Duplicate node ID '{identifier}'.", row=index, field="id")); fatal = True; continue
            attributes = self._attributes(raw.get("attributes", {}), messages, index, "node")
            if attributes is None:
                fatal = True; continue
            node_ids.add(identifier)
            nodes.append(GraphNode(identifier, self._text(raw.get("label")) or identifier, self._optional_text(raw.get("kind")), self._optional_text(raw.get("group")), attributes))

        edges: list[GraphEdge] = []
        seen_edges: set[tuple[object, ...]] = set()
        for index, raw in enumerate(raw_edges, start=1):
            if not isinstance(raw, dict):
                messages.append(AdapterMessage("error", "Edge must be an object.", row=index)); fatal = True; continue
            for field in sorted(set(raw) - self.edge_fields):
                messages.append(AdapterMessage("warning", f"Unsupported edge field '{field}' was ignored.", row=index, field=field))
            source, target = self._text(raw.get("source")), self._text(raw.get("target"))
            if not source or not target:
                messages.append(AdapterMessage("error", "Edge source and target must be nonempty.", row=index)); fatal = True; continue
            unknown = [item for item in (source, target) if item not in node_ids]
            if unknown:
                messages.append(AdapterMessage("error", f"Edge references unknown node '{unknown[0]}'.", row=index)); fatal = True; continue
            attributes = self._attributes(raw.get("attributes", {}), messages, index, "edge")
            if attributes is None:
                fatal = True; continue
            edge = GraphEdge(source, target, self._optional_text(raw.get("label")), self._optional_text(raw.get("kind")), attributes)
            key = (source, target, edge.label or "", edge.kind or "", tuple(sorted(attributes.items())))
            if key in seen_edges:
                messages.append(AdapterMessage("warning", "Duplicate edge collapsed.", row=index))
            else:
                seen_edges.add(key); edges.append(edge)

        graph_attributes = self._attributes(data.get("graph_attributes", {}), messages, None, "graph")
        node_attributes = self._attributes(data.get("node_attributes", {}), messages, None, "node defaults")
        edge_attributes = self._attributes(data.get("edge_attributes", {}), messages, None, "edge defaults")
        if None in (graph_attributes, node_attributes, edge_attributes):
            fatal = True
        directed = data.get("directed", True)
        if not isinstance(directed, bool):
            messages.append(AdapterMessage("error", "'directed' must be true or false.", field="directed")); fatal = True
        if fatal:
            return self._failure(description, messages)
        name = self._text(data.get("name")) or (request.source_path.stem if request.source_path else "Graph")
        graph = GraphDocument(name, nodes, edges, directed, graph_attributes=graph_attributes or {}, node_attributes=node_attributes or {}, edge_attributes=edge_attributes or {})
        return AdapterResult(True, graph, serialize_dot(graph), messages, description, self.name)

    def _attributes(self, value: object, messages: list[AdapterMessage], row: int | None, context: str) -> dict[str, str] | None:
        if not isinstance(value, dict):
            messages.append(AdapterMessage("error", f"{context.title()} attributes must be an object.", row=row, field="attributes")); return None
        result: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not ATTRIBUTE_NAME.fullmatch(key):
                messages.append(AdapterMessage("error", f"Invalid Graphviz attribute name '{key}'.", row=row, field=str(key))); return None
            if isinstance(item, (dict, list)):
                messages.append(AdapterMessage("error", f"{context.title()} attribute values must be scalar.", row=row, field=str(key))); return None
            result[key] = "" if item is None else str(item).lower() if isinstance(item, bool) else str(item)
        return result

    @staticmethod
    def _text(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    def _optional_text(self, value: object) -> str | None:
        return self._text(value) or None

    def _failure(self, description: str, messages: list[AdapterMessage]) -> AdapterResult:
        return AdapterResult(False, None, "", messages, description, self.name)
