"""Tests for Day 4 declarations, assignment, and output."""

import pytest

from pynative.interpreter import Interpreter, RuntimeError
from pynative.lexer import Lexer
from pynative.parser import Parser


def run(source: str) -> Interpreter:
    """Run a complete program and return its interpreter state."""
    interpreter = Interpreter()
    interpreter.execute(Parser(Lexer(source).scan_tokens()).parse_program())
    return interpreter


def test_declares_assigns_and_prints_variables() -> None:
    interpreter = run("let x = 10; x = x + 5; print(x);")

    assert interpreter.environment == {"x": 15}
    assert interpreter.output == ["15"]


def test_rejects_assignment_to_undefined_variable() -> None:
    with pytest.raises(RuntimeError, match="Undefined variable 'x'"):
        run("x = 1;")
