from __future__ import annotations

from pathlib import Path
import unittest

from limndot.adapters.registry import AdapterRegistry


class RegistryTests(unittest.TestCase):
    def test_builtins_extension_and_explicit_resolution(self) -> None:
        registry = AdapterRegistry()
        self.assertEqual({adapter.name for adapter in registry.available()}, {"CSV Relationships", "JSON Graph"})
        self.assertEqual(registry.resolve(Path("map.csv")).name, "CSV Relationships")
        self.assertEqual(registry.resolve(Path("map.json")).name, "JSON Graph")
        self.assertEqual(registry.resolve(None, "JSON Graph").name, "JSON Graph")
        self.assertIsNone(registry.resolve(Path("map.yaml")))
        self.assertIsNone(registry.resolve(None, "Missing"))


if __name__ == "__main__": unittest.main()
