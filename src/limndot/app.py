"""LIMNDOT QApplication setup and desktop entry point."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from . import __version__
from .main_window import MainWindow


# A deliberately small adaptation of LIMNINDEX's neutral Fusion family theme.
STYLE = """
QMainWindow, QWidget {
    background: #f5f6f4;
    color: #202523;
    font-size: 13px;
}
QMenuBar, QMenu, QStatusBar, QToolBar {
    background: #ffffff;
}
QToolBar {
    border: 0;
    border-bottom: 1px solid #cfd6d2;
    spacing: 8px;
    padding: 5px 10px;
}
QPlainTextEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #bfc8c3;
    border-radius: 4px;
    padding: 5px;
    selection-background-color: #2b7868;
}
QWidget#graphPreview, QScrollArea#previewScroll, QSvgWidget#svgCanvas {
    background: #eef1ef;
    border: 0;
}
QLabel#previewEmptyState {
    color: #68726e;
    background: #eef1ef;
}
QFrame#renderStatusPanel {
    background: #ffffff;
    border-top: 1px solid #cfd6d2;
}
QLabel#renderStateLabel[state="rendering"] { color: #8a5100; font-weight: 600; }
QLabel#renderStateLabel[state="ready"] { color: #185b4d; font-weight: 600; }
QLabel#renderStateLabel[state="failed"] { color: #9a2d32; font-weight: 600; }
QPlainTextEdit#renderErrors {
    color: #8c252b;
    background: #fff8f7;
    border-color: #d7b1b3;
}
QLabel#generatedStatus {
    color: #185b4d;
    background: #e7f1ed;
    border-bottom: 1px solid #b8cbc3;
    font-weight: 600;
}
QPlainTextEdit#importMessages {
    color: #6b4b00;
    background: #fffdf4;
    border-color: #d8c99b;
}
QSplitter::handle { background: #cfd6d2; width: 5px; }
"""


def configure_application(app: QApplication) -> None:
    """Apply LIMN desktop-family identity and neutral visual treatment."""
    app.setApplicationName("LIMNDOT")
    app.setApplicationDisplayName("LIMNDOT")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("LIMNMEDIA")
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f6f4"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f2f1"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#202523"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#202523"))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="limndot")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    app = QApplication.instance() or QApplication(["limndot"])
    configure_application(app)
    window = MainWindow()
    window.show()
    if args.smoke_test:
        QTimer.singleShot(1200, app.quit)
    return app.exec()
