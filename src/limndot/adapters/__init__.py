"""Built-in structured-data adapters."""

from .base import AdapterMessage, AdapterRequest, AdapterResult, GraphAdapter
from .graph_json import JsonGraphAdapter
from .registry import AdapterRegistry
from .relationships_csv import CsvRelationshipAdapter

__all__ = ["AdapterMessage", "AdapterRequest", "AdapterResult", "GraphAdapter", "JsonGraphAdapter", "AdapterRegistry", "CsvRelationshipAdapter"]
