from __future__ import annotations

import shutil
import unittest

from limndot.dot_serializer import serialize_dot
from limndot.graph_model import GraphDocument, GraphEdge, GraphNode
from limndot.renderer import GraphvizRenderer


class DotSerializerTests(unittest.TestCase):
    def make_graph(self, directed: bool = True) -> GraphDocument:
        return GraphDocument(
            "System Map",
            [GraphNode("graph", 'Café "Camera"', "device", "Capture", {"color": "red"}), GraphNode("app", "应用", "application")],
            [GraphEdge("app", "graph", "controls\nnow", attributes={"weight": "2"})],
            directed,
            graph_attributes={"rankdir": "TB"},
        )

    def test_directed_reserved_escaping_unicode_attributes_and_cluster(self) -> None:
        dot = serialize_dot(self.make_graph())
        self.assertTrue(dot.startswith('digraph "System Map"'))
        self.assertIn('"graph" [', dot)
        self.assertIn('label="Café \\"Camera\\""', dot)
        self.assertIn('label="应用"', dot)
        self.assertIn('subgraph "cluster_1"', dot)
        self.assertIn('rankdir="TB"', dot)
        self.assertIn('color="red"', dot)
        self.assertIn('weight="2"', dot)
        self.assertIn('label="controls\\nnow"', dot)

    def test_undirected_and_deterministic_order(self) -> None:
        graph = self.make_graph(False)
        first = serialize_dot(graph)
        second = serialize_dot(GraphDocument(graph.name, list(reversed(graph.nodes)), list(reversed(graph.edges)), False, graph_attributes=graph.graph_attributes))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("graph "))
        self.assertIn('"app" -- "graph"', first)

    def test_duplicate_nodes_and_edges_collapse(self) -> None:
        graph = GraphDocument("G", [GraphNode("a", "First"), GraphNode("a", "Second")], [GraphEdge("a", "a"), GraphEdge("a", "a")])
        dot = serialize_dot(graph)
        self.assertEqual(dot.count('"a" [label='), 1)
        self.assertEqual(dot.count('"a" -> "a"'), 1)

    def test_invalid_attribute_name_rejected(self) -> None:
        graph = GraphDocument("G", [GraphNode("a", "A", attributes={"x]; evil": "1"})], [])
        with self.assertRaises(ValueError): serialize_dot(graph)

    @unittest.skipUnless(shutil.which("dot"), "Graphviz dot is not installed")
    def test_graphviz_accepts_generated_dot(self) -> None:
        result = GraphvizRenderer().render(serialize_dot(self.make_graph()))
        self.assertTrue(result.success, result.error_text)


if __name__ == "__main__": unittest.main()
