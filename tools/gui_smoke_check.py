"""Bounded offscreen functional check for the Milestone 4 workflow."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import traceback

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from limndot.app import configure_application
from limndot.documents import INITIAL_DOT
from limndot.main_window import MainWindow
from limndot.settings import SettingsKeys, SettingsStore


def main() -> int:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    csv_text = "source,target,label,source_group,target_group\ncamera,app,controls,Capture,Software\ncamera,app,controls,Capture,Software\n"
    csv_path = root / "system.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    json_path = root / "graph.json"
    json_path.write_text(json.dumps({"name": "JSON Map", "nodes": [{"id": "a"}, {"id": "b"}], "edges": [{"source": "a", "target": "b", "label": "links"}]}), encoding="utf-8")
    malformed_path = root / "malformed.json"
    malformed_path.write_text("{bad", encoding="utf-8")
    endpoint_path = root / "endpoint.json"
    endpoint_path.write_text('{"nodes":[{"id":"a"}],"edges":[{"source":"a","target":"missing"}]}', encoding="utf-8")

    settings_path = root / "settings.ini"
    store = SettingsStore(QSettings(str(settings_path), QSettings.Format.IniFormat))
    app = QApplication.instance() or QApplication(["limndot-gui-smoke-check"])
    configure_application(app)
    window = MainWindow(settings_store=store)
    window.show()
    outcome = {"code": 1, "phase": "csv", "active_before_failure": None}

    def fail() -> None:
        traceback.print_exc()
        app.quit()

    def check_initial() -> None:
        try:
            assert window.preview.has_graph
            assert window.render_state.text() == "Ready"
            assert window.save_to_path(root / "baseline.dot")
            window.importFinished.connect(import_finished)
            assert window.import_path(csv_path)
        except Exception:
            fail()

    def import_finished(result: object) -> None:
        try:
            phase = outcome["phase"]
            if phase == "csv":
                assert result.success, result.error_text
                QTimer.singleShot(900, check_csv)
            elif phase == "json":
                assert result.success, result.error_text
                QTimer.singleShot(900, check_json)
            elif phase == "malformed":
                assert not result.success
                assert window.document is outcome["active_before_failure"]
                assert "Malformed JSON" in window.error_output.toPlainText()
                outcome["phase"] = "endpoint"
                QTimer.singleShot(100, lambda: window.import_path(endpoint_path))
            elif phase == "endpoint":
                assert not result.success
                assert window.document is outcome["active_before_failure"]
                assert "unknown node" in window.error_output.toPlainText()
                QTimer.singleShot(100, check_preview_regression)
        except Exception:
            fail()

    def check_csv() -> None:
        try:
            assert window.document.is_generated
            assert window.document.source_text == csv_text
            assert window.editor_tabs.indexOf(window.source_view) >= 0
            assert window.source_view.toPlainText() == csv_text
            assert "digraph" in window.editor.toPlainText()
            assert window.preview.has_graph and window.render_state.text() == "Ready"
            assert window.import_messages.isVisible()
            assert "Duplicate edge" in window.import_messages.toPlainText()
            original_source = csv_path.read_text(encoding="utf-8")
            window.editor.appendPlainText("// manual refinement")
            assert window.document.diverged
            assert "modified" in window.generated_status.text()
            dot_path = root / "system.dot"
            assert window.save_to_path(dot_path)
            assert dot_path.exists()
            assert csv_path.read_text(encoding="utf-8") == original_source
            window.exportFinished.connect(export_finished)
            assert window.export_to_path(root / "system.svg", "svg")
        except Exception:
            fail()

    def export_finished(result: object) -> None:
        try:
            assert result.success, result.error_text
            assert result.destination.exists()
            window.convert_to_dot_document()
            assert not window.document.is_generated
            assert window.editor_tabs.indexOf(window.source_view) < 0
            assert not window.convert_action.isEnabled()
            outcome["phase"] = "json"
            QTimer.singleShot(100, lambda: window.import_path(json_path))
        except Exception:
            fail()

    def check_json() -> None:
        try:
            assert window.document.is_generated
            assert window.document.adapter_name == "JSON Graph"
            assert "JSON Map" in window.editor.toPlainText()
            assert window.preview.has_graph and window.render_state.text() == "Ready"
            outcome["active_before_failure"] = window.document
            outcome["phase"] = "malformed"
            assert window.import_path(malformed_path)
        except Exception:
            fail()

    def check_preview_regression() -> None:
        try:
            window.preview.actual_size()
            window.preview.zoom_in()
            assert window.preview.zoom_percent == 125
            window.preview.zoom_out()
            assert window.preview.zoom_percent == 100
            window.preview.fit_to_window()
            assert window.preview.mode == "fit"
            window.editor.setPlainText("digraph Broken { source -> ; }")
            QTimer.singleShot(900, check_invalid_dot)
        except Exception:
            fail()

    def check_invalid_dot() -> None:
        try:
            assert window.render_state.text() == "Failed"
            assert window.preview.has_graph
            window.editor.setPlainText(INITIAL_DOT)
            assert window.save_to_path(root / "final.dot")
            QTimer.singleShot(1000, finish)
        except Exception:
            fail()

    def finish() -> None:
        try:
            assert window.render_state.text() == "Ready"
            window.save_settings()
            reloaded = SettingsStore(QSettings(str(settings_path), QSettings.Format.IniFormat))
            assert reloaded.text(SettingsKeys.IMPORT_FOLDER) == str(root)
            assert reloaded.text(SettingsKeys.LAST_ADAPTER) == "JSON Graph"
            assert reloaded.text(SettingsKeys.PREVIEW_MODE) == "fit"
            assert window.close()
            outcome["code"] = 0
            print("GUI smoke check passed: CSV/JSON translation, source/DOT views, warnings, divergence, save isolation, conversion, import failures, export, preview recovery, settings, and clean shutdown.")
            app.quit()
        except Exception:
            fail()

    QTimer.singleShot(1000, check_initial)
    QTimer.singleShot(24000, app.quit)
    app.exec()
    temporary.cleanup()
    return outcome["code"]


if __name__ == "__main__":
    raise SystemExit(main())
