"""Graphviz-backed graph export independent from the GUI."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile

from .renderer import GraphvizRenderer

EXPORT_FILTERS = {
    "SVG Image (*.svg)": "svg",
    "PNG Image (*.png)": "png",
    "PDF Document (*.pdf)": "pdf",
}


@dataclass(frozen=True, slots=True)
class ExportResult:
    success: bool
    destination: Path
    output_format: str
    error_text: str = ""
    return_code: int | None = None


def export_format_for_selection(path: Path | str, selected_filter: str = "") -> str:
    suffix = Path(path).suffix.lower().lstrip(".")
    if suffix in {"svg", "png", "pdf"}:
        return suffix
    return EXPORT_FILTERS.get(selected_filter, "svg")


def ensure_export_extension(path: Path | str, output_format: str) -> Path:
    destination = Path(path)
    return destination.with_suffix(f".{output_format}") if not destination.suffix else destination


def export_graph(
    dot_source: str,
    engine: str,
    destination: Path | str,
    output_format: str,
    *,
    renderer: GraphvizRenderer | None = None,
) -> ExportResult:
    destination_path = ensure_export_extension(destination, output_format)
    if not dot_source.strip():
        return ExportResult(False, destination_path, output_format, "Export Error: DOT source is empty.")
    rendered = (renderer or GraphvizRenderer()).render(dot_source, engine=engine, output_format=output_format)
    if not rendered.success:
        return ExportResult(False, destination_path, output_format, rendered.error_text, rendered.return_code)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination_path.parent,
            prefix=f".{destination_path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(rendered.rendered_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination_path)
        temporary_path = None
    except OSError as error:
        return ExportResult(False, destination_path, output_format, f"Export Error: could not write '{destination_path}': {error}", rendered.return_code)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return ExportResult(True, destination_path, output_format, return_code=rendered.return_code)
