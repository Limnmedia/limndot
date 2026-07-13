from __future__ import annotations

import unittest

from limndot.graph_model import GraphDocument, GraphEdge, GraphNode


class GraphModelTests(unittest.TestCase):
    def test_directed_undirected_metadata_groups_and_attributes(self) -> None:
        node = GraphNode("camera", "Camera", "device", "Capture", {"shape": "box3d"})
        edge = GraphEdge("camera", "display", "feeds", attributes={"color": "blue"})
        graph = GraphDocument("System", [node], [edge], False, {"source": "test"}, {"rankdir": "TB"})
        self.assertFalse(graph.directed)
        self.assertEqual(graph.nodes[0].identifier, "camera")
        self.assertEqual(graph.nodes[0].group, "Capture")
        self.assertEqual(graph.nodes[0].attributes["shape"], "box3d")
        self.assertEqual(graph.edges[0].attributes["color"], "blue")
        self.assertEqual(graph.metadata["source"], "test")


if __name__ == "__main__": unittest.main()
