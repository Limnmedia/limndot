"""Small language-neutral graph representation used by adapters."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GraphNode:
    identifier: str
    label: str
    kind: str | None = None
    group: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    label: str | None = None
    kind: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class GraphDocument:
    name: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    directed: bool = True
    metadata: dict[str, object] = field(default_factory=dict)
    graph_attributes: dict[str, str] = field(default_factory=dict)
    node_attributes: dict[str, str] = field(default_factory=dict)
    edge_attributes: dict[str, str] = field(default_factory=dict)
