"""Tests for Phase 2 generic syntax and specialization."""

from pynative.generics import Monomorphizer
from pynative.lexer import Lexer
from pynative.parser import Parser
from pynative.semantic import INT, STRING


def parse(source: str):
    return Parser(Lexer(source).scan_tokens()).parse_program()


def test_parses_generic_function_signature() -> None:
    program = parse("func id<T>(value: T): T { return value; }")
    function = program.statements[0]

    assert function.type_parameters[0].lexeme == "T"
    assert function.parameter_types[0].lexeme == "T"
    assert function.return_type.lexeme == "T"


def test_lazily_monomorphizes_each_concrete_instantiation_once() -> None:
    program = parse("func id<T>(value: T): T { return value; }")
    monomorphizer = Monomorphizer.from_program(program)
    function = program.statements[0]
    token = function.name

    integer = monomorphizer.specialize("id", (INT,), token)
    assert integer.name == "id_int"
    assert monomorphizer.specialize("id", (INT,), token) is integer
    assert monomorphizer.specialize("id", (STRING,), token).name == "id_string"
    assert len(monomorphizer.specializations) == 2
