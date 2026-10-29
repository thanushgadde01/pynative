"""Token definitions shared by the lexer and future parser."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """Every lexical token understood by the v0.1 language."""

    EOF = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    LET = auto()
    FUNC = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    PRINT = auto()
    TRUE = auto()
    FALSE = auto()

    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    SEMICOLON = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    AND_AND = auto()
    OR_OR = auto()


@dataclass(frozen=True, slots=True)
class Token:
    """A token, its source spelling, decoded literal value, and location."""

    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int

