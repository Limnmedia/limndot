from __future__ import annotations

import unittest

from limndot.preview_state import PreviewNavigationState


class PreviewNavigationTests(unittest.TestCase):
    def test_fit_and_zoom_transitions(self) -> None:
        state = PreviewNavigationState()
        self.assertEqual(state.mode, "fit")
        self.assertEqual(state.zoom_in(), 125)
        self.assertEqual(state.mode, "zoom")
        state.fit()
        self.assertEqual(state.mode, "fit")
        state.actual_size()
        self.assertEqual((state.mode, state.zoom_percent), ("zoom", 100))

    def test_zoom_bounds(self) -> None:
        state = PreviewNavigationState(mode="zoom", zoom_percent=800)
        self.assertEqual(state.zoom_in(), 800)
        state.set_zoom(5000)
        self.assertEqual(state.zoom_percent, 800)
        state.set_zoom(-1)
        self.assertEqual(state.zoom_percent, 10)
        self.assertEqual(state.zoom_out(), 10)


if __name__ == "__main__":
    unittest.main()
