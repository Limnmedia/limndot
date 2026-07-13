"""Typed QSettings access for lightweight LIMNDOT preferences."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QSettings


class SettingsKeys:
    GEOMETRY = "window/geometry"
    WINDOW_STATE = "window/state"
    SPLITTER_STATE = "window/splitter"
    ENGINE = "render/engine"
    OPEN_FOLDER = "folders/open"
    SAVE_FOLDER = "folders/save"
    EXPORT_FOLDER = "folders/export"
    IMPORT_FOLDER = "folders/import"
    LAST_ADAPTER = "import/adapter"
    EDITOR_TAB = "import/editor_tab"
    VALIDATION_EXPANDED = "import/validation_expanded"
    PREVIEW_MODE = "preview/mode"
    PREVIEW_ZOOM = "preview/zoom"


class SettingsStore:
    def __init__(self, settings: QSettings | None = None) -> None:
        self.settings = settings or QSettings("LIMNMEDIA", "LIMNDOT")

    def text(self, key: str, default: str = "") -> str:
        return str(self.settings.value(key, default))

    def integer(self, key: str, default: int) -> int:
        return int(self.settings.value(key, default))

    def boolean(self, key: str, default: bool) -> bool:
        value = self.settings.value(key, default)
        return value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes"}

    def bytes(self, key: str) -> QByteArray:
        value = self.settings.value(key, QByteArray())
        return value if isinstance(value, QByteArray) else QByteArray(value)

    def set(self, key: str, value: object) -> None:
        self.settings.setValue(key, value)

    def sync(self) -> None:
        self.settings.sync()
