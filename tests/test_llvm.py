"""Tests for Phase 4 LLVM emission."""

from pynative.lexer import Lexer
from pynative.llvm import lower_to_llvm_ir
from pynative.parser import Parser


def test_emits_llvm_integer_addition() -> None:
    program = Parser(Lexer("let x = 2 + 3;").scan_tokens()).parse_program()
    output = lower_to_llvm_ir(program)

    assert 'define i64 @main()' in output
    assert "add i64 2, 3" in output
    assert "ret i64 0" in output
