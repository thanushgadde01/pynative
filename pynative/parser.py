"""Recursive-descent parser for PyNative expressions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .ast_nodes import (
    AssignStmt,
    BinaryExpr,
    Expression,
    ExpressionStmt,
    GroupingExpr,
    LetStmt,
    LiteralExpr,
    PrintStmt,
    Program,
    Statement,
    UnaryExpr,
    VariableExpr,
)
from .tokens import Token, TokenType


@dataclass(frozen=True, slots=True)
class ParseError(Exception):
    """A source-location-aware syntax error."""

    message: str
    token: Token

    def __str__(self) -> str:
        return f"{self.message} at line {self.token.line}, column {self.token.column}."


class Parser:
    """Build a precedence-correct expression tree from a stream of tokens."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse_expression(self) -> Expression:
        """Parse exactly one complete expression."""
        expression = self._or()
        if not self._is_at_end():
            raise ParseError("Expected end of expression", self._peek())
        return expression

    def parse_program(self) -> Program:
        """Parse every statement in a source file."""
        statements: list[Statement] = []
        while not self._is_at_end():
            statements.append(self._statement())
        return Program(tuple(statements))

    def _statement(self) -> Statement:
        if self._match(TokenType.LET):
            name = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'")
            self._consume(TokenType.EQUAL, "Expected '=' after variable name")
            initializer = self._or()
            self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
            return LetStmt(name, initializer)
        if self._match(TokenType.PRINT):
            self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'print'")
            expression = self._or()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after print value")
            self._consume(TokenType.SEMICOLON, "Expected ';' after print statement")
            return PrintStmt(expression)
        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.EQUAL):
            name = self._advance()
            self._advance()
            value = self._or()
            self._consume(TokenType.SEMICOLON, "Expected ';' after assignment")
            return AssignStmt(name, value)
        expression = self._or()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExpressionStmt(expression)

    def _or(self) -> Expression:
        return self._binary(self._and, TokenType.OR_OR)

    def _and(self) -> Expression:
        return self._binary(self._equality, TokenType.AND_AND)

    def _equality(self) -> Expression:
        return self._binary(self._comparison, TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL)

    def _comparison(self) -> Expression:
        return self._binary(
            self._term,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        )

    def _term(self) -> Expression:
        return self._binary(self._factor, TokenType.PLUS, TokenType.MINUS)

    def _factor(self) -> Expression:
        return self._binary(self._unary, TokenType.STAR, TokenType.SLASH)

    def _binary(
        self, operand: Callable[[], Expression], *operators: TokenType
    ) -> Expression:
        left = operand()
        while self._match(*operators):
            operator = self._previous()
            left = BinaryExpr(left, operator, operand())
        return left

    def _unary(self) -> Expression:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            return UnaryExpr(operator, self._unary())
        return self._primary()

    def _primary(self) -> Expression:
        if self._match(TokenType.FALSE):
            return LiteralExpr(False)
        if self._match(TokenType.TRUE):
            return LiteralExpr(True)
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return LiteralExpr(self._previous().literal)
        if self._match(TokenType.IDENTIFIER):
            return VariableExpr(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expression = self._or()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return GroupingExpr(expression)
        raise ParseError("Expected expression", self._peek())

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParseError(message, self._peek())

    def _match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        return not self._is_at_end() and self._peek().type == token_type

    def _check_next(self, token_type: TokenType) -> bool:
        return self.current + 1 < len(self.tokens) and self.tokens[self.current + 1].type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]
