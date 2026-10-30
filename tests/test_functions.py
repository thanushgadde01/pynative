"""Tests for Day 6 functions, calls, and returns."""

import pytest

from pynative.interpreter import Interpreter, RuntimeError
from pynative.lexer import Lexer
from pynative.parser import Parser


def run(source: str) -> Interpreter:
    interpreter = Interpreter()
    interpreter.execute(Parser(Lexer(source).scan_tokens()).parse_program())
    return interpreter


def test_calls_function_with_local_parameters() -> None:
    assert run("func add(a, b) { return a + b; } print(add(2, 3));").output == ["5"]


def test_recursion_runs_capstone_program() -> None:
    source = (
        "func sum_to(n) { if (n <= 0) { return 0; } else { return n + sum_to(n - 1); } } "
        'let result = sum_to(5); print("Sum is: " + result);'
    )
    assert run(source).output == ["Sum is: 15"]


def test_rejects_wrong_function_arity() -> None:
    with pytest.raises(RuntimeError, match="Expected 2 arguments but got 1"):
        run("func add(a, b) { return a + b; } add(1);")
