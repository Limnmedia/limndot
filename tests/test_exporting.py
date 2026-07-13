from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from limndot.exporting import (
    ensure_export_extension,
    export_format_for_selection,
    export_graph,
)
from limndot.documents import DotDocument
from limndot.renderer import RenderResult


VALID_DOT = "digraph G { source -> target; }"


class FailingRenderer:
    def render(self, dot_source: str, engine: str, output_format: str) -> RenderResult:
        return RenderResult(False, b"", "Graphviz Error: invalid input", engine, output_format, 1)


class ExportUnitTests(unittest.TestCase):
    def test_export_format_selection(self) -> None:
        self.assertEqual(export_format_for_selection("graph.png", ""), "png")
        self.assertEqual(export_format_for_selection("graph", "PDF Document (*.pdf)"), "pdf")
        self.assertEqual(export_format_for_selection("graph", ""), "svg")
        self.assertEqual(ensure_export_extension("graph", "pdf"), Path("graph.pdf"))

    def test_export_failure_preserves_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "graph.svg"
            destination.write_bytes(b"previous")
            result = export_graph(VALID_DOT, "dot", destination, "svg", renderer=FailingRenderer())
            self.assertFalse(result.success)
            self.assertEqual(destination.read_bytes(), b"previous")

    def test_empty_export_does_not_create_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "empty.svg"
            result = export_graph("  ", "dot", destination, "svg")
            self.assertFalse(result.success)
            self.assertFalse(destination.exists())

    def test_export_does_not_change_document_state(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            document = DotDocument.new()
            original_path = document.path
            original_modified = document.modified
            result = export_graph(document.text, "dot", Path(folder) / "graph.svg", "svg")
            if shutil.which("dot"):
                self.assertTrue(result.success, result.error_text)
            self.assertEqual(document.path, original_path)
            self.assertEqual(document.modified, original_modified)


@unittest.skipUnless(shutil.which("dot"), "Graphviz dot is not installed")
class ExportIntegrationTests(unittest.TestCase):
    def test_svg_png_and_pdf_export(self) -> None:
        signatures = {"png": b"\x89PNG", "pdf": b"%PDF"}
        with tempfile.TemporaryDirectory() as folder:
            for output_format in ("svg", "png", "pdf"):
                with self.subTest(output_format=output_format):
                    destination = Path(folder) / f"graph.{output_format}"
                    result = export_graph(VALID_DOT, "dot", destination, output_format)
                    self.assertTrue(result.success, result.error_text)
                    content = destination.read_bytes()
                    if output_format == "svg":
                        self.assertIn(b"<svg", content)
                    else:
                        self.assertTrue(content.lstrip().startswith(signatures[output_format]))

    def test_invalid_dot_creates_no_output_or_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "invalid.svg"
            result = export_graph("digraph G { a -> ; }", "dot", destination, "svg")
            self.assertFalse(result.success)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_successful_export_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "graph.svg"
            result = export_graph(VALID_DOT, "dot", destination, "svg")
            self.assertTrue(result.success, result.error_text)
            self.assertEqual(list(Path(folder).iterdir()), [destination])


if __name__ == "__main__":
    unittest.main()
