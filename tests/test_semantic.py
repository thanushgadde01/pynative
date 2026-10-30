"""Tests for Phase 1 typed frontend analysis."""

import pytest

from pynative.lexer import Lexer
from pynative.parser import Parser
from pynative.semantic import BOOL, FLOAT, INT, STRING, SemanticError, analyze


def typed(source: str):
    program = Parser(Lexer(source).scan_tokens()).parse_program()
    return analyze(program)


def test_infers_literal_and_arithmetic_types() -> None:
    result = typed('let x = 5; let y = x + 3.2; print(y);')

    let_x, let_y = result.program.statements[:2]
    assert result.declaration_types[let_x] == INT
    assert result.declaration_types[let_y] == FLOAT


def test_checks_conditionals_and_functions() -> None:
    result = typed("func add(a, b) { return a + b; } if (true) { print(add(2, 3)); }")

    function = result.program.statements[0]
    assert result.declaration_types[function].return_type == INT


def test_rejects_invalid_numeric_operand() -> None:
    with pytest.raises(SemanticError, match="Operand must be a number"):
        typed("let invalid = 5 + true;")


def test_preserves_string_concatenation_type() -> None:
    result = typed('let message = "value: " + 5;')

    assert result.declaration_types[result.program.statements[0]] == STRING
    assert result.expression_types[result.program.statements[0].initializer] == STRING


def test_rejects_non_boolean_condition() -> None:
    with pytest.raises(SemanticError, match="Expected bool"):
        typed("if (1) print(1);")
