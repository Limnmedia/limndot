# LIMNDOT workflow-conflict audit

Date: 2026-07-24  
Repository: `https://github.com/Limnmedia/LIMNDOT.git`  
Revision: `c7260cf` (`main`, `chore: license LIMNDOT under MPL-2.0`)  
Host: Apple Silicon Mac (`arm64`), macOS 26.5.2, Xcode 26.6

## Executive result

No direct runtime workflow conflict was found between LIMNDOT and the current
LIMNTPS, SHOOTSWITCH, LIMNMOCO, or Dragonframe implementations. LIMNDOT is a
local Python/PySide6 graph workbench. It does not access cameras, BLE, USB,
serial devices, Dragonframe, TCP ports, shared databases, or background
services.

LIMNDOT should therefore be treated as an independent analysis and graph-
authoring tool. Its current scope explicitly ends at graph creation, editing,
import, export, validation, and visualization.

## Findings

### WF-001 — macOS installation path is not implemented

Severity: High before installation; no conflict during source use.

Evidence: `pyproject.toml` defines only a Python console entry point,
`limndot = limndot.__main__:main`. The repository contains no macOS app
target, `.app` bundle, Info.plist, entitlements, launch agent, installer,
DMG, signing, or notarization configuration.

Impact: A native installed Mac application cannot be claimed yet. The first
safe target is an isolated developer run from a virtual environment. A native
`.app` requires a deliberate packaging and signing workstream.

Remediation: Add packaging only after the workflow boundary is accepted.
Use a unique bundle identifier such as `com.limnmedia.limndot`, keep the app
foreground-only, and add no camera, Bluetooth, automation, network, or file-
system entitlements unless a future feature requires them.

### WF-002 — This Mac does not meet the declared runtime prerequisites

Severity: High for local build.

Evidence: LIMNDOT requires Python `>=3.13` and PySide6. This Mac currently
has `/usr/bin/python3` version 3.9.6, no detected Python 3.13, and no
PySide6 installation. Graphviz is installed and available as
`/opt/homebrew/bin/dot` version 14.1.5.

The test suite cannot run under the current interpreter: Python 3.9 reports
`dataclass() got an unexpected keyword argument 'slots'`, and the environment
also lacks PySide6.

Remediation: Install or select a supported arm64 CPython 3.13, create a
project-local `.venv`, install the project editable with its declared
dependencies, then run the tests and GUI smoke check. Do not alter the
system Python.

### WF-003 — README setup is Windows-specific

Severity: Medium.

Evidence: `README.md` documents `py -3.13`, Windows virtual-environment paths,
and PowerShell commands only.

Impact: A Mac developer can infer the required dependencies but does not have
a supported copy-paste setup path. This increases the chance of installing
into the wrong interpreter or system environment.

Remediation: Add a macOS/Linux setup section using `python3.13 -m venv .venv`,
`.venv/bin/python -m pip install -e .`, `.venv/bin/python -m unittest ...`,
and `.venv/bin/python -m limndot`. Keep the Windows instructions intact.

### WF-004 — No direct shared-settings collision with LIMNTPS was found

Severity: Informational.

Evidence: LIMNDOT uses Qt settings organization/application identity
`LIMNMEDIA` / `LIMNDOT`. LIMNTPS is a separate Flutter application with bundle
identifier `com.limnmedia.limntps`; it does not share LIMNDOT's QSettings
namespace.

Conclusion: Preferences, window geometry, import folders, and selected
Graphviz engine are locally owned by LIMNDOT and should remain so.

### WF-005 — LIMNDOT's examples may be mistaken for live integrations

Severity: Low, documentation clarity.

Evidence: The example graph models include `camera`, `dragonframe`, and
`motion_control`, while LIMNDOT's scope says it is independent of external
production and workflow systems.

Impact: Users may infer that importing or rendering a graph controls those
systems. The code does not perform such actions.

Remediation: Label examples as conceptual diagrams and add an explicit note
that node names are data only; LIMNDOT does not connect to or control the
represented systems.

## Responsibility map

| Responsibility | Owning system | LIMNDOT relationship |
|---|---|---|
| Camera setup, Hot Set, STCARD, and recovery | LIMNTPS | Conceptual graph data only |
| Physical SHOOT/GRAB controls and USB/BLE protocol | SHOOTSWITCH | No runtime dependency |
| Dragonframe capture bridge | SHOOTSWITCH desktop bridge / Dragonframe | No runtime dependency |
| Motion-control firmware | LIMNMOCO | No runtime dependency |
| Relationship graph authoring and Graphviz visualization | LIMNDOT | Sole owner |
| CSV/JSON/DOT/SVG/PNG/PDF file exchange | LIMNDOT | Explicit file-based boundary |

## Safety and macOS review

- Graphviz is invoked with `shell=False`, through stdin, with a timeout; this
  avoids shell interpretation of imported DOT content.
- CSV and JSON import is bounded and does not execute formulas, links,
  commands, environment expansions, or remote resources.
- Export uses a same-directory temporary file and atomic replacement.
- No network, Bluetooth, camera, serial, USB, automation, or launch-service
  capability was found in the source.
- No macOS signing, entitlements, bundle identifier, or installer exists yet;
  these must be introduced deliberately and reviewed before distribution.

## Required remediation order

1. Add supported macOS setup instructions.
2. Provision arm64 Python 3.13 and an isolated project virtual environment.
3. Run the complete unit suite and GUI smoke test with Graphviz available.
4. Decide whether a developer-only `.app` is needed; do not add a background
   service or ecosystem integration.
5. If packaging is approved, add a unique bundle identity, minimal entitlements,
   code-signing verification, and a clean install/uninstall test.
6. Clarify the conceptual status of the camera/Dragonframe example graphs.

## Installation gate

LIMNDOT is not approved for native installation yet. The workflow audit passes
for ecosystem isolation, but the Mac build gate remains blocked by the missing
Python 3.13/PySide6 environment and the absence of a macOS packaging target.

## PC synchronization note

This report was created on the Mac and pushed from the LIMNDOT `main` checkout.
On the PC, synchronize before doing additional work:

```powershell
git switch main
git pull --ff-only origin main
```

Review `WORKFLOW_CONFLICT_AUDIT.md` before installing or packaging LIMNDOT.
The report is an audit artifact only; it does not authorize native installation
or signing. Keep the Mac and PC checkouts on the same branch and pull before
starting work on either machine. Do not use `git reset --hard` to resolve a
divergence; preserve local work, inspect the divergence, and merge or rebase
intentionally.
