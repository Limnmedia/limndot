from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from limndot.document_controller import DocumentController
from limndot.exporting import export_graph
from limndot.import_controller import ImportController
from limndot.renderer import GraphvizRenderer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("dot"), "Graphviz dot is not installed")
class ExampleTests(unittest.TestCase):
    def test_bundled_csv_and_json_import_and_render(self) -> None:
        for name in ("system_map.csv", "camera_system.json"):
            with self.subTest(name=name):
                imported = ImportController().import_path(PROJECT_ROOT / "examples" / name)
                self.assertTrue(imported.success, imported.error_text)
                rendered = GraphvizRenderer().render(imported.document.text)
                self.assertTrue(rendered.success, rendered.error_text)

    def test_unicode_and_space_paths_import_save_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder) / "LIMNDOT café workspace"
            workspace.mkdir()
            sources = {
                "关系 map.csv": "source,target,label\ncafé,東京,connects\n",
                "关系 graph.json": '{"nodes":[{"id":"café"},{"id":"東京"}],"edges":[{"source":"café","target":"東京"}]}',
            }
            for name, content in sources.items():
                with self.subTest(name=name):
                    source = workspace / name
                    source.write_text(content, encoding="utf-8")
                    imported = ImportController().import_path(source)
                    self.assertTrue(imported.success, imported.error_text)
                    destination = workspace / f"{source.stem} output.dot"
                    saved = DocumentController(imported.document).save(destination)
                    self.assertTrue(saved.success, saved.error_text)
                    exported = export_graph(imported.document.text, "dot", workspace / f"{source.stem} preview.svg", "svg")
                    self.assertTrue(exported.success, exported.error_text)
                    self.assertEqual(source.read_text(encoding="utf-8"), content)


if __name__ == "__main__": unittest.main()
