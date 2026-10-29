"""Tests for Day 2 recursive-descent expression parsing."""

import re

import pytest

from pynative.ast_nodes import BinaryExpr, GroupingExpr, LiteralExpr, UnaryExpr, VariableExpr
from pynative.ast_printer import format_expression
from pynative.lexer import Lexer
from pynative.parser import ParseError, Parser
from pynative.tokens import TokenType


def parse(source: str):
    """Lex and parse a complete expression."""
    return Parser(Lexer(source).scan_tokens()).parse_expression()


def test_multiplication_binds_more_tightly_than_addition() -> None:
    expression = parse("1 + 2 * 3")

    assert expression == BinaryExpr(
        LiteralExpr(1),
        expression.operator.__class__(TokenType.PLUS, "+", None, 1, 3),
        BinaryExpr(
            LiteralExpr(2),
            expression.right.operator,
            LiteralExpr(3),
        ),
    )
    assert format_expression(expression) == "(+ 1 (* 2 3))"


def test_parentheses_override_precedence() -> None:
    expression = parse("(1 + 2) * 3")

    assert isinstance(expression, BinaryExpr)
    assert expression.operator.type == TokenType.STAR
    assert isinstance(expression.left, GroupingExpr)
    assert format_expression(expression) == "(* (group (+ 1 2)) 3)"


def test_parses_unary_boolean_and_variable_expressions() -> None:
    expression = parse("!enabled || -count >= 2")

    assert format_expression(expression) == "(|| (! enabled) (>= (- count) 2))"
    assert isinstance(expression, BinaryExpr)
    assert isinstance(expression.left, UnaryExpr)
    assert isinstance(expression.left.right, VariableExpr)


@pytest.mark.parametrize(
    ("source", "message"),
    [("1 +", "Expected expression"), ("(1 + 2", "Expected ')'"), ("1 2", "Expected end")],
)
def test_reports_invalid_expression(source: str, message: str) -> None:
    with pytest.raises(ParseError, match=re.escape(message)):
        parse(source)
