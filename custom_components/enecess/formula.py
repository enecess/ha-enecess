"""Bounded arithmetic formulas interpreted without executing Python code."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math
import operator

FORMULA_RESULT_TYPES = (
    "power",
    "energy",
    "reactive_energy",
    "apparent_energy",
    "apparent_power",
    "reactive_power",
    "voltage",
    "current",
    "power_factor",
    "frequency",
    "number",
)
MAX_EXPRESSION_LENGTH = 1024
MAX_NODES = 256
MAX_DEPTH = 32
_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_ARITY = {"abs": (1, 1), "min": (2, MAX_NODES), "max": (2, MAX_NODES), "round": (1, 2)}


class FormulaError(ValueError):
    """The formula or its current inputs cannot produce a finite number."""


@dataclass(frozen=True)
class ValidatedFormula:
    """A syntax-checked expression and the inputs it actually uses."""

    tree: ast.Expression
    referenced_variables: frozenset[str]


def build_formula_variables(sources: list[str]) -> dict[str, str]:
    """Assign spreadsheet-style lower-case names in selected source order."""
    variables = {}
    for index, source in enumerate(sources, 1):
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(97 + remainder) + name
        variables[name] = source
    return variables


def _number(value: object) -> float:
    if type(value) not in (int, float):
        raise FormulaError("Expected a numeric scalar")
    try:
        number = float(value)
    except (ValueError, OverflowError) as err:
        raise FormulaError("Invalid numeric scalar") from err
    if not math.isfinite(number):
        raise FormulaError("Expected a finite number")
    return number


def validate_formula(expression: str, variables: Iterable[str]) -> ValidatedFormula:
    """Accept only small arithmetic expressions using known input names."""
    if (
        not isinstance(expression, str)
        or not expression.strip()
        or len(expression) > MAX_EXPRESSION_LENGTH
    ):
        raise FormulaError("Formula is empty or too long")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except (SyntaxError, ValueError, RecursionError) as err:
        raise FormulaError("Invalid formula syntax") from err
    allowed = set(variables)
    referenced = set()
    count = 0

    def check(node: ast.AST, depth: int = 0) -> None:
        nonlocal count
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise FormulaError("Formula is too complex")
        if isinstance(node, ast.Constant):
            _number(node.value)
        elif isinstance(node, ast.Name):
            if node.id not in allowed:
                raise FormulaError("Unknown variable")
            referenced.add(node.id)
        elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            check(node.left, depth + 1)
            check(node.right, depth + 1)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            check(node.operand, depth + 1)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _ARITY
        ):
            low, high = _ARITY[node.func.id]
            if node.keywords or not low <= len(node.args) <= high:
                raise FormulaError("Invalid function arguments")
            for argument in node.args:
                check(argument, depth + 1)
        else:
            raise FormulaError("Unsupported expression")

    check(tree.body)
    if not referenced:
        raise FormulaError("Formula must reference a source")
    return ValidatedFormula(tree, frozenset(referenced))


def evaluate_formula(
    expression: str | ValidatedFormula, values: Mapping[str, float]
) -> float:
    """Interpret a validated tree with finite scalar inputs and results."""
    formula = (
        validate_formula(expression, values)
        if isinstance(expression, str)
        else expression
    )
    if not isinstance(formula, ValidatedFormula):
        raise FormulaError("Invalid formula")

    def calculate(node: ast.AST) -> float:
        if isinstance(node, ast.Constant):
            result = node.value
        elif isinstance(node, ast.Name):
            result = values[node.id]
        elif isinstance(node, ast.BinOp):
            result = _BINARY[type(node.op)](calculate(node.left), calculate(node.right))
        elif isinstance(node, ast.UnaryOp):
            result = _UNARY[type(node.op)](calculate(node.operand))
        elif isinstance(node, ast.Call):
            args = [calculate(argument) for argument in node.args]
            if node.func.id == "round":
                if len(args) == 2:
                    if not args[1].is_integer() or abs(args[1]) > 308:
                        raise FormulaError("Invalid rounding precision")
                    result = round(args[0], int(args[1]))
                else:
                    result = round(args[0])
            else:
                result = {"abs": abs, "min": min, "max": max}[node.func.id](*args)
        else:
            raise FormulaError("Unsupported expression")
        return _number(result)

    try:
        return calculate(formula.tree.body)
    except (ArithmeticError, KeyError, TypeError, ValueError, RecursionError) as err:
        raise FormulaError("Formula cannot be evaluated") from err
