from __future__ import annotations

import shutil
import subprocess
import unittest

from limndot.renderer import GraphvizRenderer


VALID_DOT = "digraph G { source -> target; }"


class RendererUnitTests(unittest.TestCase):
    def test_output_argument_construction(self) -> None:
        self.assertEqual(
            GraphvizRenderer.build_arguments("dot", "svg"), ["dot", "-Tsvg"]
        )
        self.assertEqual(
            GraphvizRenderer.build_arguments("neato", "pdf"), ["neato", "-Tpdf"]
        )

    def test_unsupported_output_argument_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            GraphvizRenderer.build_arguments("dot", "exe")

    def test_graphviz_is_invoked_without_shell(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        def runner(
            arguments: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[bytes]:
            calls.append((arguments, kwargs))
            return subprocess.CompletedProcess(arguments, 0, b"<svg/>", b"")

        renderer = GraphvizRenderer(executable_finder=lambda _: "dot", runner=runner)
        result = renderer.render(VALID_DOT)

        self.assertTrue(result.success)
        self.assertEqual(calls[0][0], ["dot", "-Tsvg"])
        self.assertIs(calls[0][1]["shell"], False)
        self.assertEqual(calls[0][1]["input"], VALID_DOT.encode("utf-8"))

    def test_unavailable_graphviz_executable_is_handled(self) -> None:
        renderer = GraphvizRenderer(executable_finder=lambda _: None)
        result = renderer.render(VALID_DOT)

        self.assertFalse(result.success)
        self.assertIsNone(result.return_code)
        self.assertIn("not found", result.error_text)

    def test_empty_source_is_handled_without_starting_process(self) -> None:
        def unexpected(_: str) -> str | None:
            self.fail("Graphviz lookup should not run for empty input")

        renderer = GraphvizRenderer(executable_finder=unexpected)
        result = renderer.render("  \n")

        self.assertFalse(result.success)
        self.assertIn("empty", result.error_text)


class RendererIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("dot"), "Graphviz dot is not installed")
    def test_valid_dot_renders_to_svg(self) -> None:
        result = GraphvizRenderer().render(VALID_DOT)

        self.assertTrue(result.success, result.error_text)
        self.assertEqual(result.return_code, 0)
        self.assertIn(b"<svg", result.rendered_bytes)

    @unittest.skipUnless(shutil.which("dot"), "Graphviz dot is not installed")
    def test_invalid_dot_returns_graphviz_error(self) -> None:
        result = GraphvizRenderer().render("digraph G { source -> ; }")

        self.assertFalse(result.success)
        self.assertNotEqual(result.return_code, 0)
        self.assertEqual(result.rendered_bytes, b"")
        self.assertTrue(result.error_text.startswith("Graphviz Error:"))


if __name__ == "__main__":
    unittest.main()
