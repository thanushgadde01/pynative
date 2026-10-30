"""Tests for Day 5 conditional control flow."""

from pynative.interpreter import Interpreter
from pynative.lexer import Lexer
from pynative.parser import Parser


def run(source: str) -> Interpreter:
    """Run a source program."""
    interpreter = Interpreter()
    interpreter.execute(Parser(Lexer(source).scan_tokens()).parse_program())
    return interpreter


def test_executes_true_branch_and_block() -> None:
    interpreter = run('let score = 10; if (score >= 10) { print("pass"); } else { print("fail"); }')

    assert interpreter.output == ["pass"]


def test_executes_false_else_branch() -> None:
    interpreter = run('if (false) print("wrong"); else print("right");')

    assert interpreter.output == ["right"]
