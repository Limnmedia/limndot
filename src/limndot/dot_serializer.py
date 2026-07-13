"""Deterministic safe Graphviz DOT serialization."""

from __future__ import annotations

import re
from collections.abc import Mapping

from .graph_model import GraphDocument, GraphEdge, GraphNode

ATTRIBUTE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_GRAPH_ATTRIBUTES = {"rankdir": "LR", "pad": "0.3", "nodesep": "0.45", "ranksep": "0.65"}
DEFAULT_NODE_ATTRIBUTES = {"shape": "box", "style": "rounded,filled", "fillcolor": "#ffffff"}
DEFAULT_EDGE_ATTRIBUTES = {"arrowsize": "0.7"}
KIND_SHAPES = {"application": "component", "device": "box3d", "file": "note", "process": "box", "person": "ellipse"}


def quote(value: object) -> str:
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n")
    return f'"{escaped}"'


def _attributes(attributes: Mapping[str, object]) -> str:
    pieces: list[str] = []
    for key in sorted(attributes):
        if not ATTRIBUTE_NAME.fullmatch(key):
            raise ValueError(f"Invalid Graphviz attribute name: {key}")
        pieces.append(f"{key}={quote(attributes[key])}")
    return ", ".join(pieces)


def _statement(name: str, attributes: Mapping[str, object], indent: str = "    ") -> str:
    return f"{indent}{name} [{_attributes(attributes)}];"


def _node_line(node: GraphNode, indent: str = "    ") -> str:
    attributes: dict[str, object] = {"label": node.label}
    if node.kind and node.kind in KIND_SHAPES:
        attributes["shape"] = KIND_SHAPES[node.kind]
    attributes.update(node.attributes)
    return f"{indent}{quote(node.identifier)} [{_attributes(attributes)}];"


def _edge_line(edge: GraphEdge, connector: str) -> str:
    attributes: dict[str, object] = dict(edge.attributes)
    if edge.label is not None:
        attributes["label"] = edge.label
    suffix = f" [{_attributes(attributes)}]" if attributes else ""
    return f"    {quote(edge.source)} {connector} {quote(edge.target)}{suffix};"


def serialize_dot(graph: GraphDocument) -> str:
    """Serialize with first-node-wins identity and deterministic ordering."""
    graph_type = "digraph" if graph.directed else "graph"
    connector = "->" if graph.directed else "--"
    lines = [f"{graph_type} {quote(graph.name)} {{"]

    graph_attributes = {**DEFAULT_GRAPH_ATTRIBUTES, **graph.graph_attributes}
    node_attributes = {**DEFAULT_NODE_ATTRIBUTES, **graph.node_attributes}
    edge_attributes = {**DEFAULT_EDGE_ATTRIBUTES, **graph.edge_attributes}
    lines.extend((_statement("graph", graph_attributes), _statement("node", node_attributes), _statement("edge", edge_attributes), ""))

    unique_nodes: dict[str, GraphNode] = {}
    for node in graph.nodes:
        unique_nodes.setdefault(node.identifier, node)
    groups: dict[str, list[GraphNode]] = {}
    ungrouped: list[GraphNode] = []
    for node in unique_nodes.values():
        (groups.setdefault(node.group, []) if node.group else ungrouped).append(node)

    for index, group in enumerate(sorted(groups), start=1):
        lines.append(f"    subgraph {quote(f'cluster_{index}')} {{")
        lines.append(f"        label={quote(group)};")
        for node in sorted(groups[group], key=lambda item: item.identifier):
            lines.append(_node_line(node, "        "))
        lines.append("    }")
        lines.append("")
    for node in sorted(ungrouped, key=lambda item: item.identifier):
        lines.append(_node_line(node))
    if ungrouped:
        lines.append("")

    unique_edges: dict[tuple[object, ...], GraphEdge] = {}
    for edge in graph.edges:
        key = (edge.source, edge.target, edge.label or "", edge.kind or "", tuple(sorted(edge.attributes.items())))
        unique_edges.setdefault(key, edge)
    for key in sorted(unique_edges):
        lines.append(_edge_line(unique_edges[key], connector))
    lines.append("}")
    return "\n".join(lines) + "\n"
