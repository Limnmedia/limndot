from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from limndot.adapters.base import AdapterRequest
from limndot.adapters.relationships_csv import CsvRelationshipAdapter


class CsvAdapterTests(unittest.TestCase):
    def generate(self, text: str):
        return CsvRelationshipAdapter().generate(AdapterRequest(Path("map.csv"), text))

    def test_minimal_optional_fields_whitespace_bom_and_blank_rows(self) -> None:
        text = "\ufeffsource,target,source_label,target_label,label,source_group,target_group,source_kind,target_kind\n a , b , Alpha , Beta , links , One , Two , device , application\n,,,,,,,,\n"
        result = self.generate(text)
        self.assertTrue(result.success, result.messages)
        self.assertEqual([(node.identifier, node.label, node.group, node.kind) for node in result.graph.nodes], [("a", "Alpha", "One", "device"), ("b", "Beta", "Two", "application")])
        self.assertEqual(result.graph.edges[0].label, "links")

    def test_missing_headers_and_empty_source_fail(self) -> None:
        self.assertFalse(self.generate("from,to\na,b\n").success)
        self.assertFalse(self.generate("").success)

    def test_empty_identifier_and_malformed_row_warn_and_skip(self) -> None:
        result = self.generate("source,target\na,\na,b,extra\na,c\n")
        self.assertTrue(result.success)
        self.assertEqual(len(result.graph.edges), 1)
        self.assertGreaterEqual(len(result.messages), 2)

    def test_duplicates_and_conflicts_warn_first_wins(self) -> None:
        text = "source,target,source_label,source_group,label\na,b,First,One,x\na,b,Second,Two,x\n"
        result = self.generate(text)
        self.assertTrue(result.success)
        self.assertEqual(len(result.graph.edges), 1)
        self.assertEqual(result.graph.nodes[0].label, "First")
        self.assertTrue(any("conflicting label" in message.message for message in result.messages))
        self.assertTrue(any("Duplicate edge" in message.message for message in result.messages))

    def test_unexpected_column_warns_and_output_is_deterministic(self) -> None:
        text = "source,target,extra\nb,c,x\na,b,y\n"
        first, second = self.generate(text), self.generate(text)
        self.assertEqual(first.generated_dot, second.generated_dot)
        self.assertTrue(any("Unexpected column" in message.message for message in first.messages))

    def test_configurable_node_limit(self) -> None:
        with patch("limndot.adapters.relationships_csv.MAX_NODES", 1):
            result = self.generate("source,target\na,b\n")
        self.assertFalse(result.success)
        self.assertTrue(any("limit" in message.message for message in result.messages))


if __name__ == "__main__": unittest.main()
