# macOS command-line distribution

This is the supported first-run path for LIMNDOT on Apple Silicon macOS. It
installs the Python package and exposes the `limndot` command; it does not
create a `.app`, DMG, launch agent, or signed installer.

## Prerequisites

- Apple Silicon macOS.
- Homebrew.
- Network access to GitHub and Python package indexes during installation.
- Graphviz available as the `dot` command.

Install the dependencies explicitly:

```bash
brew install python@3.13 graphviz pipx
pipx ensurepath
```

Restart Terminal after `pipx ensurepath` so its command directory is loaded.

## Install an approved revision

The repository is distributed from GitHub rather than PyPI. Use the reviewed
`v0.1.0` tag rather than an unpinned moving branch:

```bash
pipx install \
  --python "$(brew --prefix python@3.13)/bin/python3.13" \
  "git+https://github.com/Limnmedia/LIMNDOT.git@v0.1.0"
```

This creates an isolated environment containing Python 3.13, PySide6, and
LIMNDOT while exposing the `limndot` executable on `PATH`.

## Run and validate

```bash
dot -V
limndot --help
limndot --smoke-test
limndot
```

The normal command opens the Qt window and remains attached to the Terminal.
Use the application's normal quit action to close it. The smoke-test command
starts the GUI, verifies startup wiring, and exits automatically.

## Update and remove

Updates must name a reviewed commit. Replace `NEW_COMMIT` with that revision:

```bash
pipx install --force \
  --python "$(brew --prefix python@3.13)/bin/python3.13" \
  "git+https://github.com/Limnmedia/LIMNDOT.git@NEW_COMMIT"
```

Remove only LIMNDOT with:

```bash
pipx uninstall limndot
```

The package does not own graph documents, Graphviz, LIMNTPS data, SHOOTSWITCH
devices, or LIMNMOCO firmware. Uninstalling it must not remove those resources.

## Developer validation before approving a revision

From a source checkout using Python 3.13:

```bash
$(brew --prefix python@3.13)/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/gui_smoke_check.py
```

The revision is ready for command-line distribution only when the unit suite,
GUI smoke check, Graphviz rendering, CSV/JSON import, and SVG/PNG/PDF export
all pass.

## Security and scope

This path intentionally avoids code signing, entitlements, installer scripts,
Finder integration, background services, and automatic startup. Do not use
`curl | sh` or install LIMNDOT into the system Python. Keep installation and
updates inside `pipx`.
