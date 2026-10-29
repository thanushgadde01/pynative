"""Tests for Day 1 lexical analysis."""

import pytest

from pynative.lexer import Lexer, LexerError
from pynative.tokens import TokenType


def token_types(source: str) -> list[TokenType]:
    """Return the token types emitted for source text."""
    return [token.type for token in Lexer(source).scan_tokens()]


def test_lexes_declaration_expression_and_locations() -> None:
    tokens = Lexer("let x = 5 * (2 + y);").scan_tokens()

    assert [token.type for token in tokens] == [
        TokenType.LET,
        TokenType.IDENTIFIER,
        TokenType.EQUAL,
        TokenType.NUMBER,
        TokenType.STAR,
        TokenType.LEFT_PAREN,
        TokenType.NUMBER,
        TokenType.PLUS,
        TokenType.IDENTIFIER,
        TokenType.RIGHT_PAREN,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert tokens[1].lexeme == "x"
    assert tokens[3].literal == 5
    assert (tokens[0].line, tokens[0].column) == (1, 1)


def test_lexes_keywords_literals_and_operators() -> None:
    source = 'if (enabled && count >= 2.5 || !false) { print("hi\\nthere"); }'

    tokens = Lexer(source).scan_tokens()

    assert [token.type for token in tokens] == [
        TokenType.IF, TokenType.LEFT_PAREN, TokenType.IDENTIFIER, TokenType.AND_AND,
        TokenType.IDENTIFIER, TokenType.GREATER_EQUAL, TokenType.NUMBER, TokenType.OR_OR,
        TokenType.BANG, TokenType.FALSE, TokenType.RIGHT_PAREN, TokenType.LEFT_BRACE,
        TokenType.PRINT, TokenType.LEFT_PAREN, TokenType.STRING, TokenType.RIGHT_PAREN,
        TokenType.SEMICOLON, TokenType.RIGHT_BRACE, TokenType.EOF,
    ]
    assert tokens[6].literal == 2.5
    assert tokens[14].literal == "hi\nthere"


def test_skips_hash_and_double_slash_comments() -> None:
    source = "let first = 1; # explanation\n// another explanation\nlet second = 2;"

    assert token_types(source) == [
        TokenType.LET, TokenType.IDENTIFIER, TokenType.EQUAL, TokenType.NUMBER,
        TokenType.SEMICOLON, TokenType.LET, TokenType.IDENTIFIER, TokenType.EQUAL,
        TokenType.NUMBER, TokenType.SEMICOLON, TokenType.EOF,
    ]


@pytest.mark.parametrize(
    ("source", "message"),
    [("@", "Unexpected character"), ('"unterminated', "Unterminated string"), ('"\\q"', "Unsupported escape")],
)
def test_reports_invalid_source_with_location(source: str, message: str) -> None:
    with pytest.raises(LexerError, match=message) as error:
        Lexer(source).scan_tokens()

    assert (error.value.line, error.value.column) == (1, 1)
