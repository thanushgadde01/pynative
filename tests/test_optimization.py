"""Tests for Phase 5 optimization and deterministic cleanup."""

from pynative.ast_nodes import LetStmt, LiteralExpr
from pynative.lexer import Lexer
from pynative.optimization import Arena, optimize
from pynative.parser import Parser


def test_folds_integer_arithmetic() -> None:
    program = Parser(Lexer("let x = 2 + 3 * 4;").scan_tokens()).parse_program()
    optimized = optimize(program)

    statement = optimized.statements[0]
    assert isinstance(statement, LetStmt)
    assert statement.initializer == LiteralExpr(14)


def test_arena_closes_resources_in_reverse_order() -> None:
    closed: list[str] = []
    with Arena() as arena:
        arena.register(lambda: closed.append("first"))
        arena.register(lambda: closed.append("second"))

    assert closed == ["second", "first"]
