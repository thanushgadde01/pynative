"""Tests for Phase 3 MLIR text lowering."""

from pynative.lexer import Lexer
from pynative.mlir import lower_to_mlir
from pynative.parser import Parser


def lower(source: str) -> str:
    program = Parser(Lexer(source).scan_tokens()).parse_program()
    return lower_to_mlir(program)


def test_lowers_arithmetic_to_func_and_arith_dialects() -> None:
    output = lower("let x = 2 + 3;")

    assert "module {" in output
    assert "func.func @main()" in output
    assert "arith.constant 2 : i64" in output
    assert "arith.addi" in output


def test_lowers_function_and_conditional_structure() -> None:
    output = lower("func answer() { return 42; } if (true) { answer(); }")

    assert "func.func @answer()" in output
    assert "scf.if" in output
