"""Safe, GUI-independent Graphviz process execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Sequence


SUPPORTED_ENGINES = ("dot", "neato", "fdp", "sfdp", "circo", "twopi")
SUPPORTED_FORMATS = ("svg", "png", "pdf")


@dataclass(frozen=True, slots=True)
class RenderResult:
    """The complete outcome of one Graphviz invocation."""

    success: bool
    rendered_bytes: bytes
    error_text: str
    engine: str
    output_format: str
    return_code: int | None


Runner = Callable[..., subprocess.CompletedProcess[bytes]]


class GraphvizRenderer:
    """Render untrusted DOT through a locally installed Graphviz executable."""

    def __init__(
        self,
        *,
        executable_finder: Callable[[str], str | None] = shutil.which,
        runner: Runner = subprocess.run,
    ) -> None:
        self._executable_finder = executable_finder
        self._runner = runner

    @staticmethod
    def build_arguments(
        executable: str | Path,
        output_format: str,
    ) -> list[str]:
        """Build the argument vector used for a Graphviz render."""
        if output_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported Graphviz output format: {output_format}")
        return [str(executable), f"-T{output_format}"]

    def render(
        self,
        dot_source: str,
        engine: str = "dot",
        output_format: str = "svg",
        *,
        timeout: float | None = 30.0,
    ) -> RenderResult:
        """Render DOT received on stdin, returning errors instead of raising."""
        if engine not in SUPPORTED_ENGINES:
            return self._failure(
                f"Graphviz Error: unsupported engine '{engine}'.",
                engine,
                output_format,
            )
        if output_format not in SUPPORTED_FORMATS:
            return self._failure(
                f"Graphviz Error: unsupported output format '{output_format}'.",
                engine,
                output_format,
            )
        if not dot_source.strip():
            return self._failure(
                "Graphviz Error: DOT source is empty.", engine, output_format
            )

        executable = self._executable_finder(engine)
        if executable is None:
            return self._failure(
                f"Graphviz Error: executable '{engine}' was not found.",
                engine,
                output_format,
            )

        arguments = self.build_arguments(executable, output_format)
        try:
            completed = self._runner(
                arguments,
                input=dot_source.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                check=False,
                timeout=timeout,
            )
        except FileNotFoundError:
            return self._failure(
                f"Graphviz Error: executable '{engine}' was not found.",
                engine,
                output_format,
            )
        except subprocess.TimeoutExpired:
            return self._failure(
                "Graphviz Error: rendering timed out.", engine, output_format
            )
        except OSError as error:
            return self._failure(
                f"Graphviz Error: could not start '{engine}': {error}",
                engine,
                output_format,
            )

        error_text = completed.stderr.decode("utf-8", errors="replace").strip()
        success = completed.returncode == 0
        if not success and not error_text:
            error_text = f"Graphviz Error: process exited with code {completed.returncode}."
        elif not success and not error_text.startswith("Graphviz Error:"):
            error_text = f"Graphviz Error: {error_text}"

        return RenderResult(
            success=success,
            rendered_bytes=completed.stdout if success else b"",
            error_text=error_text,
            engine=engine,
            output_format=output_format,
            return_code=completed.returncode,
        )

    @staticmethod
    def _failure(
        message: str,
        engine: str,
        output_format: str,
        return_code: int | None = None,
    ) -> RenderResult:
        return RenderResult(
            success=False,
            rendered_bytes=b"",
            error_text=message,
            engine=engine,
            output_format=output_format,
            return_code=return_code,
        )


def render(
    dot_source: str,
    engine: str = "dot",
    output_format: str = "svg",
) -> RenderResult:
    """Render DOT using a default :class:`GraphvizRenderer`."""
    return GraphvizRenderer().render(dot_source, engine, output_format)

