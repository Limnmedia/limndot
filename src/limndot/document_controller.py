"""Testable document and file-operation coordination."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .documents import DotDocument, UnsavedDecision, load_document, save_document


@dataclass(frozen=True, slots=True)
class DocumentOperationResult:
    success: bool
    path: Path | None = None
    error_text: str = ""


class DocumentController:
    """Own the active document while leaving dialogs and presentation to Qt."""

    def __init__(self, document: DotDocument | None = None) -> None:
        self.document = document or DotDocument.initial()

    @property
    def window_title(self) -> str:
        marker = "*" if self.document.modified else ""
        return f"{self.document.display_name}{marker} \N{EM DASH} LIMNDOT"

    def update_text(self, text: str) -> None:
        self.document.set_text(text)

    def replace(self, document: DotDocument) -> None:
        self.document = document

    def new_document(self) -> DotDocument:
        self.document = DotDocument.new()
        return self.document

    def convert_generated(self) -> bool:
        if not self.document.is_generated:
            return False
        self.document.convert_to_dot()
        return True

    def open(self, path: Path | str) -> DocumentOperationResult:
        try:
            loaded = load_document(path)
        except (OSError, UnicodeError, ValueError) as error:
            return DocumentOperationResult(False, error_text=str(error))
        self.document = loaded
        return DocumentOperationResult(True, loaded.path)

    def save(self, path: Path | str | None = None) -> DocumentOperationResult:
        try:
            destination = save_document(self.document, path)
        except (OSError, ValueError) as error:
            return DocumentOperationResult(False, error_text=str(error))
        return DocumentOperationResult(True, destination)

    def resolve_unsaved(
        self,
        decision: UnsavedDecision,
        save_attempt: Callable[[], bool] | None = None,
    ) -> bool:
        if not self.document.modified:
            return True
        if decision is UnsavedDecision.DISCARD:
            return True
        if decision is UnsavedDecision.CANCEL:
            return False
        return bool(save_attempt and save_attempt())
