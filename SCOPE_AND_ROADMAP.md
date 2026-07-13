# LIMNDOT Scope and Roadmap

## Purpose

LIMNDOT is a lightweight desktop application for discovering and refining the structure of relationships.

It allows relationships to be expressed as simple text and immediately visualized using Graphviz. By separating logical relationships from visual layout, LIMNDOT helps users understand, evaluate, and improve the organization of complex systems.

The objective is not to create attractive diagrams.

The objective is to discover clear, stable structure.

## Design Philosophy

> A clear structure often produces a clear graph.

The graph is feedback about the underlying structure. Relationships remain constant while visualization stays exploratory: different Graphviz layout engines provide different views of the same logical graph without changing it.

When a graph becomes unnecessarily tangled or difficult to understand, it may indicate that the relationships themselves should be reconsidered.

## Primary Use Cases

LIMNDOT is intended for situations where relationships are more important than appearance, including:

- software architecture
- production pipelines
- filesystem organization
- data models
- entity relationships
- dependency graphs
- workflow design
- organizational structures
- technical planning

The common goal is understanding relationships.

## Scope

LIMNDOT is responsible for:

- graph editing through DOT source
- importing structured relationships
- deterministic DOT generation and export
- Graphviz rendering
- exploration through multiple layout engines
- validation of supported input
- preservation of graph structure and imported source
- SVG, PNG, and PDF export

Its responsibility ends at graph creation, editing, import, export, validation, and visualization.

## Non-Goals

LIMNDOT is not:

- a project manager
- a production tracker
- a pipeline manager
- a database
- a UML suite
- a whiteboard
- a presentation application
- an architecture framework
- a workflow engine
- a LIMNDESK replacement

LIMNDOT does not contain ecosystem-specific behavior. Other tools may exchange graph data with it through stable formats, but LIMNDOT remains independent.

## Current Capabilities

Completed and verified:

- a deterministic graph model with directed and undirected graphs
- typed nodes and edges
- graph, node, and edge attributes
- groups serialized as Graphviz clusters
- stable DOT serialization with safe quoting and escaping
- graph editing through DOT source
- a live Graphviz preview
- `dot`, `neato`, `fdp`, `sfdp`, `circo`, and `twopi` layout engines
- last-valid-preview preservation when current DOT is invalid
- an importer registry
- CSV relationship import
- JSON graph import
- generated-source preservation and explicit divergence marking after manual DOT edits
- atomic SVG, PNG, and PDF export
- normal `.dot` and `.gv` open/save lifecycle with unsaved-change protection

### Existing Validation

- duplicate identifiers
- unknown references
- identifier validation
- attribute validation
- import limits
- Graphviz syntax and rendering feedback

Validation reports problems without silently changing the user's source graph. CSV duplicate relationships are collapsed with warnings; JSON duplicate node identifiers and unknown references are rejected.

## Near-Term Roadmap

Near-term work should remain restrained and refine the existing workflow.

### Editing

Potential work:

- keyboard improvements
- find/search
- attribute-editing convenience
- small quality-of-life improvements

### Import

Current formats:

- CSV
- JSON

Possible future formats, only when a demonstrated need justifies them:

- YAML
- GraphML

The goal is to reduce manual graph construction, not to support every format.

### Export and External Visualizers

Current export formats:

- DOT
- SVG
- PNG
- PDF

Future interoperability may include:

- JSON graph export
- additional graph interchange formats
- Mermaid
- GraphML
- Cytoscape
- React Flow
- Qt Graphics View
- other external code or graph visualizers

These are future visualization or interchange targets. They must reuse the existing graph model rather than introduce competing internal graph representations.

### Validation

Existing validation covers supported imports and Graphviz rendering errors. Broader structural analysis is not currently implemented.

#### Future Validation

- consolidated graph-wide consistency view
- clearer user-facing validation presentation

Future validation should assist the user without altering the graph.

## Interoperability

- LIMNDOT remains an independent graph workbench.
- Other tools may import from or export to LIMNDOT.
- Future LIMN tools, including LIMNDESK, may launch, embed, or exchange graph data with LIMNDOT.
- LIMNDOT does not become responsible for those external workflows.

## Long-Term Direction

LIMNDOT should remain intentionally small.

Future work should refine the existing structural workflow rather than expand the product's responsibilities.

> LIMNDOT exists to help people think clearly about relationships before they build systems around them.

> The graph is the product.  
> The visualization is the tool.  
> The structure is the objective.
