"""Character-by-character lexer for the PyNative language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .tokens import Token, TokenType


KEYWORDS: Final = {
    "let": TokenType.LET,
    "func": TokenType.FUNC,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "print": TokenType.PRINT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}

SINGLE_CHARACTER_TOKENS: Final = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
}


@dataclass(frozen=True, slots=True)
class LexerError(Exception):
    """A source-location-aware lexical error."""

    message: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.message} at line {self.line}, column {self.column}."


class Lexer:
    """Convert source text into a list of tokens, including a trailing EOF token."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.current = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def scan_tokens(self) -> list[Token]:
        """Return all tokens in the source, raising LexerError for invalid input."""
        while not self._at_end():
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def _scan_token(self) -> None:
        start = self.current
        line = self.line
        column = self.column
        character = self._advance()

        if character in " \r\t":
            return
        if character == "\n":
            self.line += 1
            self.column = 1
            return
        if character == "#":
            self._skip_line_comment()
            return
        if character == "/" and self._match("/"):
            self._skip_line_comment()
            return
        if character == '"':
            self._string(start, line, column)
            return
        if character.isdigit():
            self._number(start, line, column)
            return
        if character.isalpha() or character == "_":
            self._identifier(start, line, column)
            return

        token_type = SINGLE_CHARACTER_TOKENS.get(character)
        if token_type is not None:
            self._add(token_type, start, line, column)
            return

        paired_tokens = {
            "!": (TokenType.BANG, TokenType.BANG_EQUAL, "="),
            "=": (TokenType.EQUAL, TokenType.EQUAL_EQUAL, "="),
            ">": (TokenType.GREATER, TokenType.GREATER_EQUAL, "="),
            "<": (TokenType.LESS, TokenType.LESS_EQUAL, "="),
            "&": (None, TokenType.AND_AND, "&"),
            "|": (None, TokenType.OR_OR, "|"),
        }
        pair = paired_tokens.get(character)
        if pair is not None:
            single, double, pair_character = pair
            if self._match(pair_character):
                self._add(double, start, line, column)
                return
            if single is not None:
                self._add(single, start, line, column)
                return

        raise LexerError(f"Unexpected character {character!r}", line, column)

    def _string(self, start: int, line: int, column: int) -> None:
        value: list[str] = []
        while not self._at_end() and self._peek() != '"':
            character = self._advance()
            if character == "\n":
                raise LexerError("Unterminated string", line, column)
            if character == "\\":
                value.append(self._escaped_character(line, column))
            else:
                value.append(character)
        if self._at_end():
            raise LexerError("Unterminated string", line, column)
        self._advance()
        self._add(TokenType.STRING, start, line, column, "".join(value))

    def _escaped_character(self, line: int, column: int) -> str:
        if self._at_end():
            raise LexerError("Unterminated string", line, column)
        character = self._advance()
        escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
        try:
            return escapes[character]
        except KeyError as error:
            raise LexerError(f"Unsupported escape \\{character}", line, column) from error

    def _number(self, start: int, line: int, column: int) -> None:
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek_next().isdigit():
            self._advance()
            while self._peek().isdigit():
                self._advance()
        lexeme = self.source[start : self.current]
        value = float(lexeme) if "." in lexeme else int(lexeme)
        self._add(TokenType.NUMBER, start, line, column, value)

    def _identifier(self, start: int, line: int, column: int) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        lexeme = self.source[start : self.current]
        self._add(KEYWORDS.get(lexeme, TokenType.IDENTIFIER), start, line, column)

    def _skip_line_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _add(
        self,
        token_type: TokenType,
        start: int,
        line: int,
        column: int,
        literal: object = None,
    ) -> None:
        self.tokens.append(
            Token(token_type, self.source[start : self.current], literal, line, column)
        )

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        character = self.source[self.current]
        self.current += 1
        self.column += 1
        return character

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _peek(self) -> str:
        return "\0" if self._at_end() else self.source[self.current]

    def _peek_next(self) -> str:
        index = self.current + 1
        return "\0" if index >= len(self.source) else self.source[index]
