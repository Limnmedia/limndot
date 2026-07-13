"""Command-line entry point for the LIMNDOT desktop application."""

from __future__ import annotations

import sys


def main() -> int:
    """Start LIMNDOT or report a missing GUI dependency clearly."""
    try:
        from .app import run
    except ModuleNotFoundError as exc:
        if exc.name and (exc.name == "PySide6" or exc.name.startswith("PySide6.")):
            print(
                "LIMNDOT requires PySide6. Install it with: "
                "python -m pip install -e .",
                file=sys.stderr,
            )
            return 2
        raise
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
