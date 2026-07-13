"""LIMNDOT main desktop window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QStyle,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .documents import (
    DotDocument,
    UnsavedDecision,
    ensure_dot_extension,
)
from .document_controller import DocumentController
from .editor import DotEditor
from .exporting import EXPORT_FILTERS, ExportResult, ensure_export_extension, export_format_for_selection
from .import_controller import ImportOperationResult
from .preview import GraphPreview
from .render_controller import RenderRequestController
from .renderer import RenderResult, SUPPORTED_ENGINES
from .settings import SettingsKeys, SettingsStore
from .workers import ExportWorker, ImportWorker, RenderWorker


class MainWindow(QMainWindow):
    """Coordinate documents, rendering, export, navigation, and settings."""

    DEBOUNCE_MILLISECONDS = 400
    exportFinished = Signal(object)
    importFinished = Signal(object)

    def __init__(self, settings_store: SettingsStore | None = None) -> None:
        super().__init__()
        self.setMinimumSize(900, 620)
        self.resize(1280, 800)
        self.document_controller = DocumentController(DotDocument.initial())
        self.settings = settings_store or SettingsStore()
        self._thread_pool = QThreadPool.globalInstance()
        self._requests = RenderRequestController()
        self._workers: dict[int, RenderWorker] = {}
        self._export_worker: ExportWorker | None = None
        self._import_worker: ImportWorker | None = None
        self._import_request_id = 0
        self._import_start_generation = 0
        self._document_generation = 0

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(self.DEBOUNCE_MILLISECONDS)
        self._debounce.timeout.connect(self._start_render)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_central_widget()
        self.editor.setPlainText(self.document.text)
        self.editor.textChanged.connect(self._editor_changed)
        self.editor_tabs.currentChanged.connect(self._editor_tab_changed)
        self.engine_selector.currentTextChanged.connect(self.schedule_render)
        self.preview.navigationChanged.connect(self._preview_navigation_changed)
        self._restore_settings()
        self._update_title()
        self.statusBar().showMessage("Ready to render DOT.")
        QTimer.singleShot(0, self._start_render)

    @property
    def document(self) -> DotDocument:
        return self.document_controller.document

    def _build_actions(self) -> None:
        style = self.style()
        self.new_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_document)
        self.open_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_document)
        self.import_action = QAction("Import Structured Data...", self)
        self.import_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_action.triggered.connect(self.import_structured_data)
        self.save_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_current)
        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_as)
        self.export_action = QAction("Export...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        self.export_action.triggered.connect(self.export_current)
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.setShortcuts([QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")])
        self.zoom_in_action.triggered.connect(self._zoom_in)
        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        self.zoom_out_action.triggered.connect(self._zoom_out)
        self.actual_size_action = QAction("Actual Size", self)
        self.actual_size_action.setShortcut(QKeySequence("Ctrl+1"))
        self.actual_size_action.triggered.connect(self._actual_size)
        self.fit_action = QAction("Fit to Window", self)
        self.fit_action.setShortcut(QKeySequence("Ctrl+0"))
        self.fit_action.triggered.connect(self._fit_to_window)
        self.convert_action = QAction("Convert to DOT Document", self)
        self.convert_action.setEnabled(False)
        self.convert_action.triggered.connect(self.convert_to_dot_document)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        for action in (self.new_action, self.open_action, self.import_action, self.save_action, self.save_as_action):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        document_menu = self.menuBar().addMenu("Document")
        document_menu.addAction(self.convert_action)
        view_menu = self.menuBar().addMenu("View")
        for action in (self.zoom_in_action, self.zoom_out_action, self.actual_size_action, self.fit_action):
            view_menu.addAction(action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main toolbar", self)
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        for action in (self.new_action, self.open_action, self.import_action, self.save_action, self.export_action):
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Graphviz engine"))
        self.engine_selector = QComboBox()
        self.engine_selector.addItems(SUPPORTED_ENGINES)
        self.engine_selector.setMinimumWidth(105)
        toolbar.addWidget(self.engine_selector)
        toolbar.addSeparator()
        toolbar.addAction(self.zoom_out_action)
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.actual_size_action)
        toolbar.addAction(self.fit_action)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.toolbar_state = QLabel("Idle")
        toolbar.addWidget(self.toolbar_state)

    def _build_central_widget(self) -> None:
        central = QWidget()
        central.setObjectName("centralRoot")
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(5)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        self.generated_status = QLabel("")
        self.generated_status.setObjectName("generatedStatus")
        self.generated_status.setContentsMargins(10, 5, 10, 5)
        self.generated_status.setVisible(False)
        left_layout.addWidget(self.generated_status)
        self.editor_tabs = QTabWidget()
        self.source_view = QPlainTextEdit()
        self.source_view.setReadOnly(True)
        self.source_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor = DotEditor()
        self.editor.setMinimumWidth(320)
        self.editor_tabs.addTab(self.editor, "DOT")
        left_layout.addWidget(self.editor_tabs, 1)
        self.splitter.addWidget(left_panel)
        self.preview = GraphPreview()
        self.preview.setMinimumWidth(320)
        self.splitter.addWidget(self.preview)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([560, 720])
        root.addWidget(self.splitter, 1)

        status_panel = QFrame()
        status_panel.setObjectName("renderStatusPanel")
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(14, 8, 14, 10)
        status_layout.setSpacing(6)
        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        self.render_state = QLabel("Ready")
        self.render_state.setObjectName("renderStateLabel")
        self.render_state.setProperty("state", "ready")
        self.render_detail = QLabel("Waiting for the initial render.")
        self.engine_status = QLabel("Engine: dot")
        status_row.addWidget(self.render_state)
        status_row.addWidget(self.render_detail, 1)
        status_row.addWidget(self.engine_status)
        status_layout.addLayout(status_row)
        self.import_messages = QPlainTextEdit()
        self.import_messages.setObjectName("importMessages")
        self.import_messages.setReadOnly(True)
        self.import_messages.setMaximumHeight(105)
        self.import_messages.setVisible(False)
        status_layout.addWidget(self.import_messages)
        self.error_output = QPlainTextEdit()
        self.error_output.setObjectName("renderErrors")
        self.error_output.setReadOnly(True)
        self.error_output.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.error_output.setMaximumHeight(105)
        self.error_output.setVisible(False)
        status_layout.addWidget(self.error_output)
        root.addWidget(status_panel)
        self.setCentralWidget(central)

    @Slot()
    def _editor_changed(self) -> None:
        self._document_generation += 1
        self.document_controller.update_text(self.editor.toPlainText())
        self._update_generated_status()
        self._update_title()
        self.schedule_render()

    @Slot(int)
    def _editor_tab_changed(self, _index: int) -> None:
        if self.document.is_generated:
            key = "source" if self.editor_tabs.currentWidget() is self.source_view else "dot"
            self.settings.set(SettingsKeys.EDITOR_TAB, key)

    @Slot()
    def schedule_render(self) -> None:
        self._debounce.start()

    @Slot()
    def _start_render(self) -> None:
        self._debounce.stop()
        source = self.editor.toPlainText()
        engine = self.engine_selector.currentText()
        request = self._requests.issue(source, engine)
        self.engine_status.setText(f"Engine: {engine}")
        if not source.strip():
            self._set_render_state("Waiting", "Current source is empty; showing last valid preview.", "failed")
            self._show_error("DOT source is empty; enter a graph to render.")
            self.statusBar().showMessage("DOT source is empty.")
            return
        self._set_render_state("Rendering", f"Request {request.request_id}", "rendering")
        self._show_error("")
        self.statusBar().showMessage(f"Rendering with {engine}...")
        worker = RenderWorker(request)
        worker.signals.result.connect(self._render_finished)
        worker.signals.error.connect(self._worker_error)
        worker.signals.finished.connect(self._worker_released)
        self._workers[request.request_id] = worker
        self._thread_pool.start(worker)

    @Slot(int, object)
    def _render_finished(self, request_id: int, result: RenderResult) -> None:
        if not self._requests.is_current(request_id):
            return
        if result.success:
            self.preview.load_svg(result.rendered_bytes)
            self._set_render_state("Ready", f"Rendered request {request_id}", "ready")
            self._show_error("")
            self.statusBar().showMessage(f"Rendered successfully with {result.engine}.")
        else:
            self._set_render_state("Failed", "Current source failed to render; showing last valid preview.", "failed")
            self._show_error(result.error_text)
            self.statusBar().showMessage("Current source failed to render; showing last valid preview.")

    @Slot(int, object, str)
    def _worker_error(self, request_id: int, error: BaseException, _details: str) -> None:
        if not self._requests.is_current(request_id):
            return
        self._set_render_state("Failed", "Unexpected renderer failure; showing last valid preview.", "failed")
        self._show_error(f"Graphviz Error: {error}")
        self.statusBar().showMessage("Unexpected renderer failure.")

    @Slot(int)
    def _worker_released(self, request_id: int) -> None:
        self._workers.pop(request_id, None)

    @Slot()
    def new_document(self) -> None:
        if self._confirm_unsaved_changes():
            self._display_document(self.document_controller.new_document())
            self.statusBar().showMessage("Created a new DOT document.")

    @Slot()
    def open_document(self) -> None:
        if not self._confirm_unsaved_changes():
            return
        folder = self.settings.text(SettingsKeys.OPEN_FOLDER, str(Path.home()))
        filename, _ = QFileDialog.getOpenFileName(self, "Open DOT Document", folder, "DOT Documents (*.dot *.gv)")
        if filename:
            self.open_path(filename)

    def open_path(self, path: Path | str) -> bool:
        result = self.document_controller.open(path)
        if not result.success:
            self._show_operation_error("File Error", f"Could not open '{path}': {result.error_text}")
            return False
        self._display_document(self.document)
        self.settings.set(SettingsKeys.OPEN_FOLDER, str(self.document.path.parent))
        self.statusBar().showMessage(f"Opened: {self.document.path}")
        return True

    @Slot()
    def import_structured_data(self) -> None:
        if not self._confirm_unsaved_changes():
            return
        folder = self.settings.text(SettingsKeys.IMPORT_FOLDER, str(Path.home()))
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Structured Data",
            folder,
            "All Supported Structured Data (*.csv *.json);;Relationship CSV (*.csv);;Graph JSON (*.json)",
        )
        if filename:
            self.import_path(filename)

    def import_path(self, path: Path | str, adapter_name: str | None = None) -> bool:
        if self._import_worker is not None:
            self.statusBar().showMessage("An import is already running.")
            return False
        self._import_request_id += 1
        request_id = self._import_request_id
        self._import_start_generation = self._document_generation
        self.import_action.setEnabled(False)
        self.toolbar_state.setText("Importing")
        self.statusBar().showMessage(f"Importing structured data: {path}")
        worker = ImportWorker(request_id, Path(path), adapter_name)
        worker.signals.result.connect(self._import_result)
        worker.signals.error.connect(self._import_error)
        worker.signals.finished.connect(self._import_released)
        self._import_worker = worker
        self._thread_pool.start(worker)
        return True

    @Slot(int, object)
    def _import_result(self, request_id: int, result: ImportOperationResult) -> None:
        if request_id != self._import_request_id or self._document_generation != self._import_start_generation:
            self.statusBar().showMessage("A stale import result was ignored.")
            return
        if not result.success or result.document is None:
            messages = "\n".join(message.display_text() for message in result.messages)
            self._show_operation_error("Import Error", messages or result.error_text)
            self.importFinished.emit(result)
            return
        self._replace_document(result.document)
        self.settings.set(SettingsKeys.IMPORT_FOLDER, str(result.document.source_path.parent))
        self.settings.set(SettingsKeys.LAST_ADAPTER, result.document.adapter_name or "")
        self.statusBar().showMessage(f"Imported with {result.document.adapter_name}: {result.document.source_path}")
        self.importFinished.emit(result)

    @Slot(int, object, str)
    def _import_error(self, request_id: int, error: BaseException, _details: str) -> None:
        if request_id == self._import_request_id:
            self._show_operation_error("Import Error", f"Import failed safely: {error}")

    @Slot(int)
    def _import_released(self, request_id: int) -> None:
        if request_id == self._import_request_id:
            self._import_worker = None
            self.import_action.setEnabled(True)
            self.toolbar_state.setText(self.render_state.text())

    @Slot()
    def save_current(self) -> bool:
        if self.document.path is None:
            return self.save_as()
        return self.save_to_path(self.document.path)

    @Slot()
    def save_as(self) -> bool:
        folder = self.settings.text(SettingsKeys.SAVE_FOLDER, str(Path.home()))
        suggested = str(Path(folder) / self.document.suggested_dot_name)
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save DOT Document",
            suggested,
            "DOT Document (*.dot);;Graphviz Document (*.gv)",
        )
        if not filename:
            return False
        preferred_extension = ".gv" if "*.gv" in selected_filter else ".dot"
        return self.save_to_path(ensure_dot_extension(filename, preferred_extension))

    def save_to_path(self, path: Path | str) -> bool:
        self.document_controller.update_text(self.editor.toPlainText())
        result = self.document_controller.save(path)
        if not result.success:
            self._show_operation_error("File Error", f"Could not save '{path}': {result.error_text}")
            return False
        destination = result.path
        self.settings.set(SettingsKeys.SAVE_FOLDER, str(destination.parent))
        self._update_title()
        self._show_error("")
        self.statusBar().showMessage(f"Saved: {destination}")
        self._update_generated_status()
        return True

    @Slot()
    def convert_to_dot_document(self) -> None:
        if not self.document_controller.convert_generated():
            return
        self._configure_document_view(self.document)
        self._update_title()
        self.statusBar().showMessage("Converted generated content to a normal DOT document.")

    @Slot()
    def export_current(self) -> None:
        folder = self.settings.text(SettingsKeys.EXPORT_FOLDER, str(Path.home()))
        stem = self.document.path.stem if self.document.path else "diagram"
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Graph",
            str(Path(folder) / f"{stem}.svg"),
            ";;".join(EXPORT_FILTERS),
        )
        if not filename:
            return
        output_format = export_format_for_selection(filename, selected_filter)
        self.export_to_path(filename, output_format)

    def export_to_path(self, path: Path | str, output_format: str | None = None) -> bool:
        if self._export_worker is not None:
            self.statusBar().showMessage("An export is already running.")
            return False
        source = self.editor.toPlainText()
        if not source.strip():
            self._show_operation_error("Export Error", "DOT source is empty.")
            return False
        output_format = output_format or export_format_for_selection(path)
        destination = ensure_export_extension(path, output_format)
        self.settings.set(SettingsKeys.EXPORT_FOLDER, str(destination.parent))
        self.export_action.setEnabled(False)
        self.toolbar_state.setText("Exporting")
        self.statusBar().showMessage(f"Exporting {output_format.upper()}...")
        worker = ExportWorker(source, self.engine_selector.currentText(), destination, output_format)
        worker.signals.result.connect(self._export_result)
        worker.signals.error.connect(self._export_error)
        worker.signals.finished.connect(self._export_released)
        self._export_worker = worker
        self._thread_pool.start(worker)
        return True

    @Slot(object)
    def _export_result(self, result: ExportResult) -> None:
        if result.success:
            self._show_error("")
            self.statusBar().showMessage(f"Exported {result.output_format.upper()}: {result.destination}")
        else:
            self._show_operation_error("Export Error", result.error_text)
        self.exportFinished.emit(result)

    @Slot(object, str)
    def _export_error(self, error: BaseException, _details: str) -> None:
        self._show_operation_error("Export Error", f"Export failed: {error}")

    @Slot()
    def _export_released(self) -> None:
        self._export_worker = None
        self.export_action.setEnabled(True)
        self.toolbar_state.setText(self.render_state.text())

    def _replace_document(self, document: DotDocument) -> None:
        self.document_controller.replace(document)
        self._display_document(document)

    def _display_document(self, document: DotDocument) -> None:
        self._document_generation += 1
        self.editor.blockSignals(True)
        self.editor.setPlainText(document.text)
        self.editor.blockSignals(False)
        self._configure_document_view(document)
        self._update_title()
        QTimer.singleShot(0, self._start_render)

    def _configure_document_view(self, document: DotDocument) -> None:
        source_index = self.editor_tabs.indexOf(self.source_view)
        if document.is_generated:
            if source_index < 0:
                self.editor_tabs.insertTab(0, self.source_view, "Imported Source")
            self.source_view.setPlainText(document.source_text or "")
            self.source_view.setToolTip(str(document.source_path or document.source_description))
            self.editor_tabs.setTabText(self.editor_tabs.indexOf(self.editor), "Generated DOT")
            selected = self.settings.text(SettingsKeys.EDITOR_TAB, "dot")
            self.editor_tabs.setCurrentWidget(self.source_view if selected == "source" else self.editor)
            self.convert_action.setEnabled(True)
            message_text = "\n".join(
                message.display_text() if hasattr(message, "display_text") else str(message)
                for message in document.adapter_messages
            )
            self.import_messages.setPlainText(message_text or "Import completed without warnings.")
            expanded = self.settings.boolean(SettingsKeys.VALIDATION_EXPANDED, True)
            self.import_messages.setVisible(expanded)
        else:
            if source_index >= 0:
                self.editor_tabs.removeTab(source_index)
            self.editor_tabs.setTabText(self.editor_tabs.indexOf(self.editor), "DOT")
            self.editor_tabs.setCurrentWidget(self.editor)
            self.convert_action.setEnabled(False)
            self.import_messages.setVisible(False)
        self._update_generated_status()

    def _update_generated_status(self) -> None:
        if not self.document.is_generated:
            self.generated_status.setVisible(False)
            return
        state = "Generated DOT modified — detached changes" if self.document.diverged else f"Generated by {self.document.adapter_name}"
        self.generated_status.setText(state)
        self.generated_status.setVisible(True)

    def _confirm_unsaved_changes(self) -> bool:
        if not self.document.modified:
            return True
        answer = QMessageBox.warning(
            self,
            "Unsaved changes",
            f"Save changes to {self.document.display_name} before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.document_controller.resolve_unsaved(UnsavedDecision.SAVE, self.save_current)
        if answer == QMessageBox.StandardButton.Discard:
            return self.document_controller.resolve_unsaved(UnsavedDecision.DISCARD)
        return self.document_controller.resolve_unsaved(UnsavedDecision.CANCEL)

    def _zoom_in(self) -> None:
        self.preview.zoom_in()

    def _zoom_out(self) -> None:
        self.preview.zoom_out()

    def _actual_size(self) -> None:
        self.preview.actual_size()

    def _fit_to_window(self) -> None:
        self.preview.fit_to_window()

    @Slot(str)
    def _preview_navigation_changed(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _update_title(self) -> None:
        self.setWindowTitle(self.document_controller.window_title)

    def _set_render_state(self, title: str, detail: str, state: str) -> None:
        self.render_state.setText(title)
        self.render_state.setProperty("state", state)
        self.render_state.style().unpolish(self.render_state)
        self.render_state.style().polish(self.render_state)
        self.render_detail.setText(detail)
        if self._export_worker is None:
            self.toolbar_state.setText(title)

    def _show_error(self, message: str) -> None:
        self.error_output.setPlainText(message)
        self.error_output.setVisible(bool(message))

    def _show_operation_error(self, category: str, message: str) -> None:
        text = message if message.startswith(category) else f"{category}: {message}"
        self._show_error(text)
        self.statusBar().showMessage(text)

    def _restore_settings(self) -> None:
        geometry = self.settings.bytes(SettingsKeys.GEOMETRY)
        if not geometry.isEmpty():
            self.restoreGeometry(geometry)
        window_state = self.settings.bytes(SettingsKeys.WINDOW_STATE)
        if not window_state.isEmpty():
            self.restoreState(window_state)
        splitter_state = self.settings.bytes(SettingsKeys.SPLITTER_STATE)
        if not splitter_state.isEmpty():
            self.splitter.restoreState(splitter_state)
        engine = self.settings.text(SettingsKeys.ENGINE, "dot")
        self.engine_selector.setCurrentText(engine if engine in SUPPORTED_ENGINES else "dot")
        mode = self.settings.text(SettingsKeys.PREVIEW_MODE, "fit")
        zoom = self.settings.integer(SettingsKeys.PREVIEW_ZOOM, 100)
        self.preview.restore_navigation(mode, zoom)

    def save_settings(self) -> None:
        self.settings.set(SettingsKeys.GEOMETRY, self.saveGeometry())
        self.settings.set(SettingsKeys.WINDOW_STATE, self.saveState())
        self.settings.set(SettingsKeys.SPLITTER_STATE, self.splitter.saveState())
        self.settings.set(SettingsKeys.ENGINE, self.engine_selector.currentText())
        self.settings.set(SettingsKeys.PREVIEW_MODE, self.preview.mode)
        self.settings.set(SettingsKeys.PREVIEW_ZOOM, self.preview.zoom_percent)
        active_tab = "source" if self.document.is_generated and self.editor_tabs.currentWidget() is self.source_view else "dot"
        self.settings.set(SettingsKeys.EDITOR_TAB, active_tab)
        self.settings.set(SettingsKeys.VALIDATION_EXPANDED, self.import_messages.isVisible())
        self.settings.sync()

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._confirm_unsaved_changes():
            event.ignore()
            return
        self.save_settings()
        event.accept()
