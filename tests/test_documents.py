from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from limndot.documents import (
    DocumentType,
    DotDocument,
    UnsavedDecision,
    ensure_dot_extension,
    load_document,
    save_document,
    unsaved_action_allows_replacement,
)
from limndot.renderer import GraphvizRenderer


class DocumentTests(unittest.TestCase):
    def test_initial_example_is_clean_until_edited(self) -> None:
        document = DotDocument.initial()
        self.assertFalse(document.modified)
        document.set_text(document.text + "// edited\n")
        self.assertTrue(document.modified)

    def test_new_document_is_unsaved_and_modified(self) -> None:
        document = DotDocument.new()
        self.assertIsNone(document.path)
        self.assertEqual(document.display_name, "Untitled")
        self.assertEqual(document.document_type, DocumentType.UNSAVED_DOT)
        self.assertTrue(document.modified)
        result = GraphvizRenderer().render(document.text)
        if result.error_text != "Graphviz Error: executable 'dot' was not found.":
            self.assertTrue(result.success, result.error_text)

    def test_modified_state_tracks_last_saved_text(self) -> None:
        document = DotDocument.loaded(Path("diagram.dot"), "digraph G {}")
        self.assertFalse(document.modified)
        document.set_text("digraph G { a; }")
        self.assertTrue(document.modified)
        document.set_text("digraph G {}")
        self.assertFalse(document.modified)

    def test_setting_and_clearing_path_via_new_document(self) -> None:
        document = DotDocument.new()
        document.set_text("digraph G {}")
        document.mark_saved(Path("map.gv"))
        self.assertEqual(document.document_type, DocumentType.GV)
        self.assertEqual(document.display_name, "map.gv")
        self.assertFalse(document.modified)
        replacement = DotDocument.new()
        self.assertIsNone(replacement.path)

    def test_dot_and_gv_load_with_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            for name, expected_type in (("a.dot", DocumentType.DOT), ("b.gv", DocumentType.GV)):
                path = Path(folder) / name
                path.write_text("\ufeffdigraph Café {}", encoding="utf-8")
                loaded = load_document(path)
                self.assertEqual(loaded.text, "digraph Café {}")
                self.assertEqual(loaded.document_type, expected_type)
                self.assertFalse(loaded.modified)

    def test_utf8_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unicode.dot"
            document = DotDocument(text='digraph G { café [label="日本語"]; }')
            save_document(document, path)
            self.assertFalse(document.modified)
            self.assertEqual(load_document(path).text, document.text)

    def test_automatic_dot_extension(self) -> None:
        self.assertEqual(ensure_dot_extension("diagram"), Path("diagram.dot"))
        self.assertEqual(ensure_dot_extension("diagram", ".gv"), Path("diagram.gv"))
        self.assertEqual(ensure_dot_extension("diagram.gv"), Path("diagram.gv"))
        with self.assertRaises(ValueError):
            ensure_dot_extension("diagram", ".txt")

    def test_save_failure_leaves_document_modified(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            document = DotDocument.new()
            with self.assertRaises(OSError):
                save_document(document, Path(folder) / "missing" / "diagram.dot")
            self.assertTrue(document.modified)
            self.assertIsNone(document.path)

    def test_unsaved_action_decision_flow(self) -> None:
        self.assertTrue(unsaved_action_allows_replacement(False, UnsavedDecision.CANCEL))
        self.assertTrue(unsaved_action_allows_replacement(True, UnsavedDecision.DISCARD))
        self.assertFalse(unsaved_action_allows_replacement(True, UnsavedDecision.CANCEL))
        self.assertFalse(unsaved_action_allows_replacement(True, UnsavedDecision.SAVE, save_succeeded=False))
        self.assertTrue(unsaved_action_allows_replacement(True, UnsavedDecision.SAVE, save_succeeded=True))


if __name__ == "__main__":
    unittest.main()
