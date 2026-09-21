"""Keep translation keys and format placeholders aligned with the source."""

import json
from pathlib import Path
import string
import unittest


ROOT = Path(__file__).resolve().parents[1] / "custom_components/enecess"


def flatten(value, prefix=""):
    result = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten(item, path))
        else:
            result[path] = item
    return result


def placeholders(value):
    return {field for _, field, _, _ in string.Formatter().parse(value) if field}


class TranslationCompletenessTests(unittest.TestCase):
    def test_all_languages_match_source_keys_and_placeholders(self):
        source = flatten(json.loads((ROOT / "strings.json").read_text(encoding="utf-8")))
        paths = sorted((ROOT / "translations").glob("*.json"))
        self.assertIn("it.json", [path.name for path in paths])
        for path in paths:
            with self.subTest(language=path.stem):
                translated = flatten(json.loads(path.read_text(encoding="utf-8")))
                self.assertEqual(source.keys(), translated.keys())
                for key, value in translated.items():
                    with self.subTest(key=key):
                        self.assertIsInstance(value, str)
                        self.assertTrue(value.strip())
                        self.assertEqual(placeholders(source[key]), placeholders(value))

    def test_english_translation_matches_source(self):
        self.assertEqual(
            json.loads((ROOT / "strings.json").read_text(encoding="utf-8")),
            json.loads((ROOT / "translations/en.json").read_text(encoding="utf-8")),
        )
