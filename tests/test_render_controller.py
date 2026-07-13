from __future__ import annotations

import unittest

from limndot.documents import INITIAL_DOT
from limndot.render_controller import RenderRequestController
from limndot.renderer import GraphvizRenderer, SUPPORTED_ENGINES


class RenderRequestControllerTests(unittest.TestCase):
    def test_request_identifiers_are_monotonic(self) -> None:
        controller = RenderRequestController()

        first = controller.issue("digraph A {}", "dot")
        second = controller.issue("digraph B {}", "neato")

        self.assertEqual(first.request_id, 1)
        self.assertEqual(second.request_id, 2)
        self.assertEqual(second.engine, "neato")

    def test_only_latest_result_is_current(self) -> None:
        controller = RenderRequestController()
        stale = controller.issue("digraph A {}", "dot")
        latest = controller.issue("digraph B {}", "dot")

        self.assertFalse(controller.is_current(stale.request_id))
        self.assertTrue(controller.is_current(latest.request_id))

    def test_default_example_is_valid_dot(self) -> None:
        result = GraphvizRenderer().render(INITIAL_DOT)
        self.assertTrue(result.success, result.error_text)
        self.assertIn(b"<svg", result.rendered_bytes)

    def test_supported_engine_order(self) -> None:
        self.assertEqual(
            SUPPORTED_ENGINES,
            ("dot", "neato", "fdp", "sfdp", "circo", "twopi"),
        )


if __name__ == "__main__":
    unittest.main()
