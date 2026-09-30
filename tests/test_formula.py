"""Offline tests for the restricted formula interpreter."""
import importlib.util
from pathlib import Path
import sys
import unittest


class FormulaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "custom_components/enecess/formula.py"
        cls.path = path

    def engine(self):
        self.assertTrue(self.path.exists(), "Restricted formula interpreter is missing")
        spec = importlib.util.spec_from_file_location("formula_under_test", self.path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_arithmetic_and_allowed_functions(self):
        engine = self.engine()
        for expression, expected in [
            ("a - b * 2 + 4 / (1 + 1)", 6),
            ("abs(-a) + min(a, b) - max(a, b)", 3),
            ("round(a / b, 2)", 3.33), ("+a + -b", 7),
        ]:
            with self.subTest(expression=expression):
                validated = engine.validate_formula(expression, ["a", "b"])
                self.assertEqual(engine.evaluate_formula(validated, {"a": 10, "b": 3}), expected)

    def test_rejects_unsupported_syntax_and_invalid_arguments(self):
        engine = self.engine()
        for expression in ["1 + 2", "a + unknown", "a ** 2", "a // 2", "a % 2",
                           "a.real", "a[0]", "[a]", "True + a", "'x' + a", "a > 0",
                           "a if a else 0", "sum(a)", "abs(a, 2)", "min()", "max(a)",
                           "round(a, 1, 2)", "round(a, ndigits=2)", "abs(*a)",
                           "__import__('os')", "(lambda: a)()", "1e999 + a", ""]:
            with self.subTest(expression=expression), self.assertRaises(engine.FormulaError):
                engine.validate_formula(expression, ["a"])

    def test_bad_values_and_nonfinite_results_raise_formula_error(self):
        engine = self.engine()
        for expression, values in [("a / b", {"a": 1, "b": 0}), ("a", {}),
                                   ("a", {"a": None}), ("a", {"a": True}),
                                   ("a", {"a": "bad"}), ("a", {"a": float("nan")}),
                                   ("a", {"a": float("inf")}),
                                   ("a * a", {"a": 1e308}), ("round(a, b)", {"a": 2, "b": 1.5})]:
            with self.subTest(expression=expression, values=values), self.assertRaises(engine.FormulaError):
                engine.evaluate_formula(expression, values)

    def test_formula_size_and_depth_are_bounded(self):
        engine = self.engine()
        for expression in ["a" + "+1" * 2000, "-" * 100 + "a", "(" * 1000 + "a" + ")" * 1000]:
            with self.assertRaises(engine.FormulaError):
                engine.validate_formula(expression, ["a"])

    def test_variables_extend_past_z_in_source_order(self):
        engine = self.engine()
        actual = engine.build_formula_variables([f"source_{i}" for i in range(28)])
        self.assertEqual(actual["a"], "source_0")
        self.assertEqual(actual["z"], "source_25")
        self.assertEqual(actual["aa"], "source_26")
        self.assertEqual(actual["ab"], "source_27")

    def test_forty_fifth_source_has_a_usable_alias(self):
        engine = self.engine()
        sources = [f"source_{i}" for i in range(45)]
        actual = engine.build_formula_variables(sources)
        expected_names = [chr(letter) for letter in range(ord("a"), ord("z") + 1)]
        expected_names += ["a" + chr(letter) for letter in range(ord("a"), ord("r") + 1)]
        self.assertEqual(list(actual)[:44], expected_names)
        alias = next(name for name, source in actual.items() if source == sources[44])
        try:
            validated = engine.validate_formula(alias, actual)
        except engine.FormulaError as error:
            self.fail(f"The generated alias {alias!r} cannot be used: {error}")
        self.assertEqual(engine.evaluate_formula(validated, {alias: 45}), 45)

    def test_all_generated_aliases_remain_usable_past_later_keywords(self):
        engine = self.engine()
        sources = [f"source_{i}" for i in range(500)]
        actual = engine.build_formula_variables(sources)
        self.assertEqual(list(actual.values()), sources)
        for index, alias in enumerate(actual, 1):
            with self.subTest(alias=alias):
                try:
                    validated = engine.validate_formula(alias, actual)
                except engine.FormulaError as error:
                    self.fail(f"The generated alias {alias!r} cannot be used: {error}")
                self.assertEqual(engine.evaluate_formula(validated, {alias: index}), index)
