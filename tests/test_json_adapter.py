from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from limndot.adapters.base import AdapterRequest
from limndot.adapters.graph_json import JsonGraphAdapter


class JsonAdapterTests(unittest.TestCase):
    def generate(self, data: object):
        text = data if isinstance(data, str) else json.dumps(data)
        return JsonGraphAdapter().generate(AdapterRequest(Path("map.json"), text))

    def valid(self) -> dict[str, object]:
        return {"name": "Map", "directed": False, "graph_attributes": {"rankdir": "TB"}, "nodes": [{"id": "a", "label": "Alpha", "group": "One", "attributes": {"shape": "ellipse"}}, {"id": "b"}], "edges": [{"source": "a", "target": "b", "label": "links", "attributes": {"color": "blue"}}]}

    def test_valid_undirected_attributes_groups_labels_and_determinism(self) -> None:
        first, second = self.generate(self.valid()), self.generate(self.valid())
        self.assertTrue(first.success, first.messages)
        self.assertFalse(first.graph.directed)
        self.assertEqual(first.graph.graph_attributes["rankdir"], "TB")
        self.assertEqual(first.graph.nodes[0].group, "One")
        self.assertEqual(first.graph.nodes[0].attributes["shape"], "ellipse")
        self.assertEqual(first.graph.edges[0].label, "links")
        self.assertEqual(first.graph.edges[0].attributes["color"], "blue")
        self.assertEqual(first.generated_dot, second.generated_dot)

    def test_malformed_json_reports_line_and_column(self) -> None:
        result = self.generate('{"nodes": [}')
        self.assertFalse(result.success)
        self.assertIn("line", result.messages[0].message)
        self.assertIn("column", result.messages[0].message)

    def test_invalid_top_nodes_and_edges_types(self) -> None:
        self.assertFalse(self.generate([]).success)
        self.assertFalse(self.generate({"nodes": {}, "edges": []}).success)
        self.assertFalse(self.generate({"nodes": [], "edges": {}}).success)

    def test_duplicate_node_and_unknown_endpoint_fail(self) -> None:
        duplicate = self.generate({"nodes": [{"id": "a"}, {"id": "a"}], "edges": []})
        unknown = self.generate({"nodes": [{"id": "a"}], "edges": [{"source": "a", "target": "missing"}]})
        self.assertFalse(duplicate.success)
        self.assertFalse(unknown.success)
        self.assertTrue(any("unknown node" in message.message for message in unknown.messages))

    def test_empty_identifier_invalid_lists_and_attribute_values_fail(self) -> None:
        self.assertFalse(self.generate({"nodes": [{"id": " "}], "edges": []}).success)
        self.assertFalse(self.generate({"nodes": [{"id": "a", "attributes": []}], "edges": []}).success)
        self.assertFalse(self.generate({"nodes": [{"id": "a", "attributes": {"bad": []}}], "edges": []}).success)
        self.assertFalse(self.generate({"nodes": [{"id": "a", "attributes": {"x]; inject": "1"}}], "edges": []}).success)

    def test_unsupported_fields_and_duplicate_edges_warn(self) -> None:
        data = {"unknown": 1, "nodes": [{"id": "a", "extra": 2}, {"id": "b"}], "edges": [{"source": "a", "target": "b"}, {"source": "a", "target": "b"}]}
        result = self.generate(data)
        self.assertTrue(result.success)
        self.assertEqual(len(result.graph.edges), 1)
        self.assertGreaterEqual(len(result.messages), 3)

    def test_configurable_limits(self) -> None:
        with patch("limndot.adapters.graph_json.MAX_NODES", 1):
            result = self.generate({"nodes": [{"id": "a"}, {"id": "b"}], "edges": []})
        self.assertFalse(result.success)


if __name__ == "__main__": unittest.main()
