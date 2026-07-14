# LIMNDOT

> LIMNDOT is a lightweight desktop application for discovering and refining the structure of relationships.

LIMNDOT is a Python 3.13 and PySide6 graph workbench. It allows relationships to
be expressed as DOT source and immediately visualized using Graphviz. It also
translates generic CSV relationship tables or explicit JSON graphs into editable,
deterministic DOT without hiding the imported source.

The objective is not decorative diagramming. The objective is to help the user
discover clear, stable structure. See [SCOPE_AND_ROADMAP.md](SCOPE_AND_ROADMAP.md)
for the product boundary and restrained roadmap.

## Requirements and setup

- Python 3.13
- Graphviz command-line tools available on `PATH`

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m limndot
```

The installed `limndot` command is also available while the virtual environment
is activated. LIMNDOT detects the selected Graphviz executable on `PATH` and
reports a visible render error if it is unavailable.

## Translation architecture

```text
CSV or JSON -> built-in adapter -> GraphDocument -> DOT serializer -> editable DOT
```

Adapters only parse and validate. They do not invoke Graphviz, write files,
execute imported content, or manipulate the GUI. The deterministic serializer
owns quoting, escaping, clustering, restrained defaults, and attribute safety.

Use **File > Import Structured Data** (`Ctrl+I`) to import `.csv` or `.json`.
A generated document shows **Imported Source** and **Generated DOT** tabs. The
source is read-only; DOT is editable and drives the normal live preview. Editing
DOT marks it as diverged and never triggers silent regeneration.

**Document > Convert to DOT Document** detaches the current DOT from its live
generated-document context without changing or deleting the imported source.
Saving a generated document always writes a separate `.dot` or `.gv` file.

## CSV relationships

Required columns:

```csv
source,target
```

Optional columns are `source_label`, `target_label`, `label`, `source_group`,
`target_group`, `source_kind`, and `target_kind`. Source and target identifiers
implicitly create nodes. Blank rows are ignored. Identical edges collapse with
a warning. Conflicting node labels, groups, or kinds retain the first value and
produce warnings. Rows missing an endpoint are skipped with a warning.

See [examples/system_map.csv](examples/system_map.csv).

## JSON graphs

JSON uses an object containing `name`, `directed`, optional graph/default
attributes, a `nodes` list, and an `edges` list. Nodes support `id`, `label`,
`group`, `kind`, and scalar Graphviz `attributes`. Edges support `source`,
`target`, `label`, `kind`, and attributes.

Node IDs must be unique. Unlike CSV, JSON edges may only reference explicitly
declared nodes. Unknown endpoints and duplicate node IDs are errors. Identical
edges collapse with a warning. Unsupported fields warn and are ignored.

See [examples/camera_system.json](examples/camera_system.json).

## Safety and limits

CSV and JSON are treated as untrusted data. LIMNDOT does not execute formulas,
expressions, macros, links, HTML, commands, environment expansions, or remote
resources. Invalid Graphviz attribute names are rejected. Current limits are:

- Source file: 20 MB
- Nodes: 10,000
- Edges: 25,000

## Editor controls

- `Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`: document operations
- `Ctrl+I`: structured import
- `Ctrl+E`: Graphviz SVG/PNG/PDF export
- `Ctrl++` / `Ctrl+-`: zoom
- `Ctrl+1`: actual size
- `Ctrl+0`: fit to window

Export uses the selected Graphviz engine, writes through a same-directory
temporary file, and atomically replaces the destination after success. It never
changes the DOT document's saved state.

## Current limitations

LIMNDOT has one active document and one preview. Graph editing is performed
through DOT source; there is no structured or visual node-and-edge property
editor. Graph search, a consolidated validation view, YAML and GraphML import,
JSON graph export, and external visualizer integrations are possible future work,
not current capabilities or MVP blockers.

LIMNDOT remains independent of external project, production, pipeline, and
workflow systems.

## License

LIMNDOT is licensed under the Mozilla Public License 2.0. See [LICENSE](LICENSE).
