# Cross-platform installation

LIMNDOT is distributed as a Python package. The application code is
platform-independent; PySide6 supplies the GUI and Graphviz supplies the
rendering engines on each target operating system.

## Requirements

- Python 3.13.
- Graphviz available on `PATH`.
- Network access to GitHub or the release artifacts.

Verify Graphviz before launching:

```text
dot -V
```

## Windows

Install Python 3.13 and Graphviz using approved installers or the machine's
package manager. From PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install "git+https://github.com/Limnmedia/LIMNDOT.git@v0.1.1"
.\.venv\Scripts\limndot.exe --help
.\.venv\Scripts\limndot.exe --smoke-test
.\.venv\Scripts\limndot.exe
```

The package installs into `.venv`; it does not modify the system Python.

## Linux

Install Python 3.13 and Graphviz with the distribution's supported package
manager. Then run:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install "git+https://github.com/Limnmedia/LIMNDOT.git@v0.1.1"
.venv/bin/limndot --help
QT_QPA_PLATFORM=offscreen .venv/bin/limndot --smoke-test
.venv/bin/limndot
```

Some Linux distributions require additional Qt runtime libraries. The GUI
smoke test will expose missing display or Qt-library dependencies before normal
use.

## macOS

See [the macOS command-line guide](MACOS_COMMAND_LINE.md). The same package
can be installed from a wheel or package index; Homebrew remains the supported
way to provide Python 3.13 and Graphviz on this development Mac.

## Upgrade and removal

Inside the environment, upgrade explicitly from a reviewed release tag:

```text
python -m pip install --upgrade "git+https://github.com/Limnmedia/LIMNDOT.git@NEW_TAG"
```

Remove LIMNDOT by deleting the project `.venv`, or use the platform's isolated
package-manager uninstall command. User-created `.dot`, `.gv`, `.csv`, `.json`,
SVG, PNG, and PDF files are not owned by the package and must remain untouched.

## Release boundary

This release does not provide `.app`, `.exe`, AppImage, Debian, or RPM
artifacts. It does not add code signing, entitlements, launch agents,
background services, or automatic startup. Native installers require a
separate platform-specific release track.
