"""GUI-independent preview fit and zoom state."""

from __future__ import annotations

from dataclasses import dataclass

ZOOM_LEVELS = (10, 25, 33, 50, 67, 80, 100, 125, 150, 200, 300, 400, 600, 800)


@dataclass(slots=True)
class PreviewNavigationState:
    mode: str = "fit"
    zoom_percent: int = 100

    def fit(self) -> None:
        self.mode = "fit"

    def actual_size(self) -> None:
        self.mode = "zoom"
        self.zoom_percent = 100

    def set_zoom(self, percent: int) -> None:
        self.mode = "zoom"
        self.zoom_percent = max(ZOOM_LEVELS[0], min(ZOOM_LEVELS[-1], int(percent)))

    def zoom_in(self) -> int:
        current = self.zoom_percent if self.mode == "zoom" else 100
        self.set_zoom(next((level for level in ZOOM_LEVELS if level > current), ZOOM_LEVELS[-1]))
        return self.zoom_percent

    def zoom_out(self) -> int:
        current = self.zoom_percent if self.mode == "zoom" else 100
        self.set_zoom(next((level for level in reversed(ZOOM_LEVELS) if level < current), ZOOM_LEVELS[0]))
        return self.zoom_percent
