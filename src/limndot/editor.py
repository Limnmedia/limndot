"""DOT source editor widget."""

from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase, QFontMetricsF
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class DotEditor(QPlainTextEdit):
    """A compact code-oriented plain-text editor for DOT source."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(" ") * 4)
        self.setPlaceholderText("Enter Graphviz DOT source...")
        self.setObjectName("dotEditor")
