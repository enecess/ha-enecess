"""Offline configuration regression tests."""

import types
import unittest
from unittest.mock import AsyncMock, patch
from flow_test_support import load_flow

class BrandMigrationTests(unittest.TestCase):
    def setUp(self):
        load_flow(self)
        import importlib
        self.registry = importlib.import_module("custom_components.enecess.registry")

    def test_default_entry_titles_updated_but_custom_titles_preserved(self):
        self.assertTrue(hasattr(self.registry, "normalize_entry_title"))
        data = {"device_type": "ecomain", "mode": "manual", "ecomain_serial": "123"}
        self.assertEqual("ecoMain 123 (Local)", self.registry.normalize_entry_title(data, "EcoMain 123 (Local)"))
        self.assertEqual("My EcoMain", self.registry.normalize_entry_title(data, "My EcoMain"))
        data = {"device_type": "ecoplug", "username": "test@example.invalid"}
        self.assertEqual("ecoPlug (test@example.invalid)", self.registry.normalize_entry_title(data, "EcoPlug (test@example.invalid)"))
