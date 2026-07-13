"""DOT document state and safe UTF-8 file operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

INITIAL_DOT = '''digraph LIMNDOT {
    rankdir=LR;

    source [label="Technical Source"];
    adapter [label="Adapter"];
    dot [label="Editable DOT"];
    graphviz [label="Graphviz"];
    output [label="Preview / Export"];

    source -> adapter;
    adapter -> dot;
    dot -> graphviz;
    graphviz -> output;
}
'''

NEW_DOT = """digraph "Graph" {
}
"""


class DocumentType(str, Enum):
    UNSAVED_DOT = "unsaved_dot"
    DOT = "dot"
    GV = "gv"
    GENERATED_DOT = "generated_dot"


class UnsavedDecision(str, Enum):
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


@dataclass(slots=True)
class DotDocument:
    """One visible DOT document with explicit clean-state tracking."""

    text: str
    path: Path | None = None
    document_type: DocumentType = DocumentType.UNSAVED_DOT
    saved_text: str = ""
    source_text: str | None = None
    source_path: Path | None = None
    source_type: str | None = None
    source_description: str = ""
    adapter_name: str | None = None
    adapter_messages: tuple[object, ...] = ()
    generated_original_text: str | None = None
    diverged: bool = False
    detached: bool = False

    @classmethod
    def initial(cls) -> "DotDocument":
        return cls(text=INITIAL_DOT, saved_text=INITIAL_DOT)

    @classmethod
    def new(cls) -> "DotDocument":
        return cls(text=NEW_DOT)

    @classmethod
    def loaded(cls, path: Path, text: str) -> "DotDocument":
        resolved = Path(path)
        return cls(text=text, path=resolved, document_type=document_type_for_path(resolved), saved_text=text)

    @classmethod
    def generated(
        cls,
        text: str,
        *,
        source_text: str,
        source_path: Path | None,
        source_type: str,
        source_description: str,
        adapter_name: str,
        adapter_messages: tuple[object, ...] = (),
    ) -> "DotDocument":
        return cls(
            text=text,
            document_type=DocumentType.GENERATED_DOT,
            source_text=source_text,
            source_path=source_path,
            source_type=source_type,
            source_description=source_description,
            adapter_name=adapter_name,
            adapter_messages=adapter_messages,
            generated_original_text=text,
        )

    @property
    def display_name(self) -> str:
        if self.path:
            return self.path.name
        if self.document_type is DocumentType.GENERATED_DOT and self.source_path:
            return f"{self.source_path.stem}.dot"
        return "Untitled"

    @property
    def is_generated(self) -> bool:
        return self.document_type is DocumentType.GENERATED_DOT

    @property
    def suggested_dot_name(self) -> str:
        return self.path.name if self.path else self.display_name if self.is_generated else "diagram.dot"

    @property
    def modified(self) -> bool:
        return self.text != self.saved_text

    def set_text(self, text: str) -> None:
        self.text = text
        if self.is_generated and self.generated_original_text is not None and text != self.generated_original_text:
            self.diverged = True

    def mark_saved(self, path: Path) -> None:
        self.path = Path(path)
        if not self.is_generated:
            self.document_type = document_type_for_path(self.path)
        self.saved_text = self.text

    def convert_to_dot(self) -> None:
        self.document_type = document_type_for_path(self.path) if self.path else DocumentType.UNSAVED_DOT
        self.detached = True
        self.adapter_messages = ()


def document_type_for_path(path: Path) -> DocumentType:
    suffix = path.suffix.lower()
    if suffix == ".gv":
        return DocumentType.GV
    if suffix == ".dot":
        return DocumentType.DOT
    raise ValueError(f"Unsupported DOT document extension: {path.suffix or '(none)'}")


def ensure_dot_extension(path: Path | str, preferred_extension: str = ".dot") -> Path:
    result = Path(path)
    if result.suffix:
        return result
    extension = preferred_extension if preferred_extension.startswith(".") else f".{preferred_extension}"
    if extension not in {".dot", ".gv"}:
        raise ValueError(f"Unsupported DOT document extension: {extension}")
    return result.with_suffix(extension)


def load_document(path: Path | str) -> DotDocument:
    source = Path(path)
    document_type_for_path(source)
    text = source.read_text(encoding="utf-8-sig")
    return DotDocument.loaded(source, text)


def save_document(document: DotDocument, path: Path | str | None = None) -> Path:
    if path is None and document.path is None:
        raise ValueError("A destination is required to save the document.")
    destination = ensure_dot_extension(path if path is not None else document.path)
    document_type_for_path(destination)
    destination.write_text(document.text, encoding="utf-8", newline="")
    document.mark_saved(destination)
    return destination


def unsaved_action_allows_replacement(
    modified: bool,
    decision: UnsavedDecision,
    *,
    save_succeeded: bool = False,
) -> bool:
    """Resolve destructive-action flow without depending on a visible dialog."""
    if not modified:
        return True
    if decision is UnsavedDecision.DISCARD:
        return True
    if decision is UnsavedDecision.SAVE:
        return save_succeeded
    return False
