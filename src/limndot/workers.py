"""Background Graphviz workers adapted from LIMNINDEX's QRunnable pattern."""

from __future__ import annotations

import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from .exporting import export_graph
from .import_controller import ImportController
from .render_controller import RenderRequest
from .renderer import GraphvizRenderer


class RenderWorkerSignals(QObject):
    result = Signal(int, object)
    error = Signal(int, object, str)
    finished = Signal(int)


class RenderWorker(QRunnable):
    def __init__(self, request: RenderRequest, renderer: GraphvizRenderer | None = None) -> None:
        super().__init__()
        self.request = request
        self.renderer = renderer or GraphvizRenderer()
        self.signals = RenderWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.renderer.render(self.request.dot_source, engine=self.request.engine, output_format="svg")
        except Exception as exc:
            self.signals.error.emit(self.request.request_id, exc, traceback.format_exc())
        else:
            self.signals.result.emit(self.request.request_id, result)
        finally:
            self.signals.finished.emit(self.request.request_id)


class ExportWorkerSignals(QObject):
    result = Signal(object)
    error = Signal(object, str)
    finished = Signal()


class ExportWorker(QRunnable):
    """Render and write one graph export without blocking the GUI thread."""

    def __init__(self, dot_source: str, engine: str, destination: Path, output_format: str) -> None:
        super().__init__()
        self.dot_source = dot_source
        self.engine = engine
        self.destination = destination
        self.output_format = output_format
        self.signals = ExportWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = export_graph(self.dot_source, self.engine, self.destination, self.output_format)
        except Exception as exc:
            self.signals.error.emit(exc, traceback.format_exc())
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class ImportWorkerSignals(QObject):
    result = Signal(int, object)
    error = Signal(int, object, str)
    finished = Signal(int)


class ImportWorker(QRunnable):
    """Read and translate one structured input away from the GUI thread."""

    def __init__(self, request_id: int, path: Path, adapter_name: str | None = None) -> None:
        super().__init__()
        self.request_id = request_id
        self.path = path
        self.adapter_name = adapter_name
        self.signals = ImportWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = ImportController().import_path(self.path, self.adapter_name)
        except Exception as exc:
            self.signals.error.emit(self.request_id, exc, traceback.format_exc())
        else:
            self.signals.result.emit(self.request_id, result)
        finally:
            self.signals.finished.emit(self.request_id)
