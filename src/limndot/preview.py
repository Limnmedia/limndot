"""Scrollable SVG preview with deterministic fit and zoom navigation."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QEvent, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent, QResizeEvent
from PySide6.QtWidgets import QLabel, QScrollArea, QStackedLayout, QWidget
from PySide6.QtSvgWidgets import QSvgWidget

from .preview_state import PreviewNavigationState


class PannableScrollArea(QScrollArea):
    """A normal scroll area with optional left- or middle-button drag panning."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._panning = False
        self._pan_origin = QPoint()

    def viewportEvent(self, event: QEvent) -> bool:
        if isinstance(event, QMouseEvent):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() in (
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.MiddleButton,
            ):
                self._panning = True
                self._pan_origin = event.position().toPoint()
                self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return True
            if event.type() == QEvent.Type.MouseMove and self._panning:
                position = event.position().toPoint()
                delta = position - self._pan_origin
                self._pan_origin = position
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
                event.accept()
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._panning:
                self._panning = False
                self.viewport().unsetCursor()
                event.accept()
                return True
        return super().viewportEvent(event)


class GraphPreview(QWidget):
    """Display SVG bytes directly while retaining navigation state."""

    navigationChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("graphPreview")
        self.navigation = PreviewNavigationState()

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._empty = QLabel("Rendering graph...")
        self._empty.setObjectName("previewEmptyState")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stack.addWidget(self._empty)

        self._svg = QSvgWidget()
        self._svg.setObjectName("svgCanvas")
        self._svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self._scroll = PannableScrollArea()
        self._scroll.setObjectName("previewScroll")
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setWidgetResizable(False)
        self._scroll.setWidget(self._svg)
        self._stack.addWidget(self._scroll)

        self._has_graph = False
        self._natural_size = QSize()

    @property
    def has_graph(self) -> bool:
        return self._has_graph

    @property
    def mode(self) -> str:
        return self.navigation.mode

    @property
    def zoom_percent(self) -> int:
        return self.navigation.zoom_percent

    def load_svg(self, svg_bytes: bytes) -> None:
        self._svg.load(QByteArray(svg_bytes))
        self._natural_size = self._svg.renderer().defaultSize()
        self._has_graph = True
        self._stack.setCurrentWidget(self._scroll)
        self._resize_canvas()

    def zoom_in(self) -> None:
        self.navigation.zoom_in()
        self._navigation_updated()

    def zoom_out(self) -> None:
        self.navigation.zoom_out()
        self._navigation_updated()

    def actual_size(self) -> None:
        self.navigation.actual_size()
        self._navigation_updated()

    def fit_to_window(self) -> None:
        self.navigation.fit()
        self._navigation_updated()

    def restore_navigation(self, mode: str, zoom_percent: int) -> None:
        if mode == "fit":
            self.navigation.fit()
        else:
            self.navigation.set_zoom(zoom_percent)
        self._resize_canvas()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self.navigation.mode == "fit":
            self._resize_canvas()

    def _navigation_updated(self) -> None:
        self._resize_canvas()
        message = "Fit to window" if self.navigation.mode == "fit" else f"Zoom: {self.navigation.zoom_percent}%"
        self.navigationChanged.emit(message)

    def _resize_canvas(self) -> None:
        if self._natural_size.isEmpty():
            return
        if self.navigation.mode == "fit":
            viewport = self._scroll.viewport().size()
            width = max(1, viewport.width() - 4)
            height = max(1, viewport.height() - 4)
            scale = min(width / self._natural_size.width(), height / self._natural_size.height())
        else:
            scale = self.navigation.zoom_percent / 100.0
        target = QSize(
            max(1, round(self._natural_size.width() * scale)),
            max(1, round(self._natural_size.height() * scale)),
        )
        self._svg.resize(target)
