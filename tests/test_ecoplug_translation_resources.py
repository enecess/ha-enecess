import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TRANSLATION_FILES = (
    ROOT / "custom_components/enecess/strings.json",
    ROOT / "custom_components/enecess/translations/en.json",
    ROOT / "custom_components/enecess/translations/de.json",
    ROOT / "custom_components/enecess/translations/fr.json",
    ROOT / "custom_components/enecess/translations/it.json",
    ROOT / "custom_components/enecess/translations/pl.json",
    ROOT / "custom_components/enecess/translations/zh-Hans.json",
)


class EcoPlugTranslationResourceTests(unittest.TestCase):
    def test_ecoplug_selection_descriptions_exist_in_both_flows(self):
        for path in TRANSLATION_FILES:
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                config_description = data["config"]["step"]["ecoplug_select"]["description"]
                options_description = data["options"]["step"]["ecoplug_select"]["description"]
                self.assertTrue(config_description.strip())
                self.assertTrue(options_description.strip())

    def test_descriptions_do_not_expose_internal_entity_identifiers(self):
        for path in TRANSLATION_FILES:
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                description = data["config"]["step"]["ecoplug_select"]["description"]
                self.assertNotIn("power_rt", description)
                self.assertNotIn("energy_total", description)
                self.assertNotIn("unique_id", description)
