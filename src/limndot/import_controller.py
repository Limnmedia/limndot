"""Safe structured-data import orchestration independent from Qt."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adapters.base import AdapterMessage, AdapterRequest, AdapterResult, MAX_SOURCE_BYTES
from .adapters.registry import AdapterRegistry
from .documents import DotDocument


@dataclass(slots=True)
class ImportOperationResult:
    success: bool
    document: DotDocument | None
    adapter_result: AdapterResult | None
    messages: list[AdapterMessage]
    error_text: str = ""


class ImportController:
    def __init__(self, registry: AdapterRegistry | None = None) -> None:
        self.registry = registry or AdapterRegistry()

    def import_path(self, path: Path | str, adapter_name: str | None = None) -> ImportOperationResult:
        source_path = Path(path)
        adapter = self.registry.resolve(source_path, adapter_name)
        if adapter is None:
            message = AdapterMessage("error", f"Unsupported structured input type: {source_path.suffix or '(none)' }.")
            return ImportOperationResult(False, None, None, [message], message.message)
        try:
            size = source_path.stat().st_size
            if size > MAX_SOURCE_BYTES:
                message = AdapterMessage("error", f"Source exceeds the {MAX_SOURCE_BYTES // (1024 * 1024)} MB size limit.")
                return ImportOperationResult(False, None, None, [message], message.message)
            source_text = source_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            message = AdapterMessage("error", f"Could not read '{source_path}': {error}")
            return ImportOperationResult(False, None, None, [message], message.message)
        try:
            result = adapter.generate(AdapterRequest(source_path, source_text, {}))
        except Exception as error:
            message = AdapterMessage("error", f"Adapter failed safely: {error}")
            return ImportOperationResult(False, None, None, [message], message.message)
        if not result.success or not result.generated_dot:
            error_text = next((message.message for message in result.messages if message.level == "error"), "Import did not produce usable DOT.")
            return ImportOperationResult(False, None, result, result.messages, error_text)
        document = DotDocument.generated(
            result.generated_dot,
            source_text=source_text,
            source_path=source_path,
            source_type=source_path.suffix.lower().lstrip("."),
            source_description=result.source_description,
            adapter_name=result.adapter_name,
            adapter_messages=tuple(result.messages),
        )
        return ImportOperationResult(True, document, result, result.messages)
