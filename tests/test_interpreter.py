"""Tests for Day 3 expression evaluation."""

import pytest

from pynative.interpreter import Interpreter, RuntimeError
from pynative.lexer import Lexer
from pynative.parser import Parser


def evaluate(source: str):
    """Lex, parse, and evaluate an expression."""
    return Interpreter().evaluate(Parser(Lexer(source).scan_tokens()).parse_expression())


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("2 + 3 * 4", 14),
        ("(2 + 3) * 4 == 20", True),
        ("!false && 1 < 2", True),
        ('"Sum: " + 15', "Sum: 15"),
    ],
)
def test_evaluates_expressions(source: str, expected: object) -> None:
    assert evaluate(source) == expected


@pytest.mark.parametrize(
    ("source", "message"),
    [("1 / 0", "Division by zero"), ("true + 1", "Operand must be a number")],
)
def test_reports_runtime_errors(source: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        evaluate(source)


def test_reports_undefined_variable() -> None:
    with pytest.raises(RuntimeError, match="Undefined variable 'missing'"):
        evaluate("missing")
