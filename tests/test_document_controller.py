from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from limndot.document_controller import DocumentController
from limndot.documents import DotDocument, UnsavedDecision


class DocumentControllerTests(unittest.TestCase):
    def test_title_and_modified_marker(self) -> None:
        controller = DocumentController(DotDocument.new())
        self.assertEqual(controller.window_title, "Untitled* \N{EM DASH} LIMNDOT")
        with tempfile.TemporaryDirectory() as folder:
            result = controller.save(Path(folder) / "diagram.dot")
            self.assertTrue(result.success, result.error_text)
            self.assertEqual(controller.window_title, "diagram.dot \N{EM DASH} LIMNDOT")
            controller.update_text("digraph Changed {}")
            self.assertEqual(controller.window_title, "diagram.dot* \N{EM DASH} LIMNDOT")

    def test_failed_open_does_not_replace_current_document(self) -> None:
        current = DotDocument.new()
        controller = DocumentController(current)
        result = controller.open("missing.dot")
        self.assertFalse(result.success)
        self.assertIs(controller.document, current)

    def test_cancelled_save_as_does_not_change_path(self) -> None:
        controller = DocumentController(DotDocument.new())
        allowed = controller.resolve_unsaved(UnsavedDecision.SAVE, lambda: False)
        self.assertFalse(allowed)
        self.assertIsNone(controller.document.path)

    def test_unsaved_save_success_failure_discard_and_cancel(self) -> None:
        controller = DocumentController(DotDocument.new())
        self.assertTrue(controller.resolve_unsaved(UnsavedDecision.SAVE, lambda: True))
        self.assertFalse(controller.resolve_unsaved(UnsavedDecision.SAVE, lambda: False))
        self.assertTrue(controller.resolve_unsaved(UnsavedDecision.DISCARD))
        self.assertFalse(controller.resolve_unsaved(UnsavedDecision.CANCEL))


if __name__ == "__main__":
    unittest.main()
