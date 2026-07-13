from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from limndot.document_controller import DocumentController
from limndot.documents import DocumentType, DotDocument
from limndot.import_controller import ImportController


class ImportAndGeneratedDocumentTests(unittest.TestCase):
    def test_csv_import_retains_source_generated_dot_and_distinct_paths(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "camera.csv"
            original = "source,target\ncamera,app\n"
            source.write_text(original, encoding="utf-8")
            result = ImportController().import_path(source)
            self.assertTrue(result.success, result.error_text)
            document = result.document
            self.assertEqual(document.document_type, DocumentType.GENERATED_DOT)
            self.assertEqual(document.source_text, original)
            self.assertEqual(document.source_path, source)
            self.assertIn("digraph", document.text)
            self.assertIsNone(document.path)
            self.assertEqual(document.suggested_dot_name, "camera.dot")

    def test_edit_diverges_save_never_overwrites_source_and_conversion_preserves_dot(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "map.csv"
            source.write_text("source,target\na,b\n", encoding="utf-8")
            document = ImportController().import_path(source).document
            original_source = source.read_text(encoding="utf-8")
            document.set_text(document.text + "// edited\n")
            self.assertTrue(document.diverged)
            controller = DocumentController(document)
            destination = Path(folder) / "map.dot"
            self.assertTrue(controller.save(destination).success)
            self.assertEqual(source.read_text(encoding="utf-8"), original_source)
            current_dot = document.text
            self.assertTrue(controller.convert_generated())
            self.assertEqual(document.text, current_dot)
            self.assertFalse(document.is_generated)
            self.assertTrue(document.detached)

    def test_failed_import_does_not_replace_active_document(self) -> None:
        active = DotDocument.new()
        controller = DocumentController(active)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.json"
            source.write_text("{bad", encoding="utf-8")
            result = ImportController().import_path(source)
        self.assertFalse(result.success)
        self.assertIs(controller.document, active)

    def test_unknown_endpoint_and_unsupported_type_fail(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "bad.json"
            bad.write_text('{"nodes":[{"id":"a"}],"edges":[{"source":"a","target":"b"}]}', encoding="utf-8")
            unsupported = Path(folder) / "graph.yaml"
            unsupported.write_text("x", encoding="utf-8")
            self.assertFalse(ImportController().import_path(bad).success)
            self.assertFalse(ImportController().import_path(unsupported).success)

    def test_source_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "large.csv"
            source.write_text("source,target\na,b\n", encoding="utf-8")
            with patch("limndot.import_controller.MAX_SOURCE_BYTES", 1):
                result = ImportController().import_path(source)
        self.assertFalse(result.success)


if __name__ == "__main__": unittest.main()
