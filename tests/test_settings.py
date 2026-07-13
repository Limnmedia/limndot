from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QByteArray, QSettings

from limndot.settings import SettingsKeys, SettingsStore


class SettingsTests(unittest.TestCase):
    def test_expected_settings_keys_are_stable(self) -> None:
        self.assertEqual(SettingsKeys.ENGINE, "render/engine")
        self.assertEqual(SettingsKeys.SPLITTER_STATE, "window/splitter")
        self.assertEqual(SettingsKeys.PREVIEW_MODE, "preview/mode")
        self.assertEqual(SettingsKeys.IMPORT_FOLDER, "folders/import")
        self.assertEqual(SettingsKeys.LAST_ADAPTER, "import/adapter")

    def test_settings_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.ini"
            first = SettingsStore(QSettings(str(path), QSettings.Format.IniFormat))
            first.set(SettingsKeys.ENGINE, "neato")
            first.set(SettingsKeys.OPEN_FOLDER, "C:/graphs")
            first.set(SettingsKeys.PREVIEW_MODE, "zoom")
            first.set(SettingsKeys.PREVIEW_ZOOM, 150)
            first.set(SettingsKeys.GEOMETRY, QByteArray(b"geometry"))
            first.set(SettingsKeys.EDITOR_TAB, "source")
            first.set(SettingsKeys.VALIDATION_EXPANDED, True)
            first.sync()
            second = SettingsStore(QSettings(str(path), QSettings.Format.IniFormat))
            self.assertEqual(second.text(SettingsKeys.ENGINE), "neato")
            self.assertEqual(second.text(SettingsKeys.OPEN_FOLDER), "C:/graphs")
            self.assertEqual(second.text(SettingsKeys.PREVIEW_MODE), "zoom")
            self.assertEqual(second.integer(SettingsKeys.PREVIEW_ZOOM, 100), 150)
            self.assertEqual(bytes(second.bytes(SettingsKeys.GEOMETRY)), b"geometry")
            self.assertEqual(second.text(SettingsKeys.EDITOR_TAB), "source")
            self.assertTrue(second.boolean(SettingsKeys.VALIDATION_EXPANDED, False))


if __name__ == "__main__":
    unittest.main()
