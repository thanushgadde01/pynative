"""Tree-walk evaluation for PyNative expressions."""

from __future__ import annotations

from dataclasses import dataclass, field

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

Value = bool | float | int | str | None


@dataclass(frozen=True, slots=True)
class RuntimeError(Exception):
    """An error raised while evaluating a program."""

    message: str
    token: Token

    def __str__(self) -> str:
        return f"{self.message} at line {self.token.line}, column {self.token.column}."


@dataclass(slots=True)
class Interpreter:
    """Evaluate PyNative expression trees using a global environment."""

    environment: dict[str, Value] = field(default_factory=dict)
    output: list[str] = field(default_factory=list)

    def execute(self, program: Program) -> None:
        """Execute a complete program in the current global environment."""
        for statement in program.statements:
            self.execute_statement(statement)

    def execute_statement(self, statement: Statement) -> None:
        """Execute one statement."""
        match statement:
            case LetStmt(name, initializer):
                self.environment[name.lexeme] = self.evaluate(initializer)
            case AssignStmt(name, value):
                if name.lexeme not in self.environment:
                    raise RuntimeError(f"Undefined variable '{name.lexeme}'", name)
                self.environment[name.lexeme] = self.evaluate(value)
            case PrintStmt(expression):
                self.output.append(self._display(self.evaluate(expression)))
            case ExpressionStmt(expression):
                self.evaluate(expression)

    def evaluate(self, expression: Expression) -> Value:
        """Evaluate one expression and return its runtime value."""
        match expression:
            case LiteralExpr(value):
                return value  # type: ignore[return-value]
            case GroupingExpr(inner):
                return self.evaluate(inner)
            case VariableExpr(name):
                try:
                    return self.environment[name.lexeme]
                except KeyError as error:
                    raise RuntimeError(f"Undefined variable '{name.lexeme}'", name) from error
            case UnaryExpr(operator, right):
                return self._unary(operator, self.evaluate(right))
            case BinaryExpr(left, operator, right):
                return self._binary(operator, self.evaluate(left), self.evaluate(right))

    def _unary(self, operator: Token, right: Value) -> Value:
        if operator.type == TokenType.BANG:
            return not self._truthy(right)
        if operator.type == TokenType.MINUS:
            return -self._number(right, operator)
        raise RuntimeError(f"Unsupported unary operator '{operator.lexeme}'", operator)

    def _binary(self, operator: Token, left: Value, right: Value) -> Value:
        match operator.type:
            case TokenType.PLUS:
                if isinstance(left, str) or isinstance(right, str):
                    return f"{self._display(left)}{self._display(right)}"
                return self._number(left, operator) + self._number(right, operator)
            case TokenType.MINUS:
                return self._number(left, operator) - self._number(right, operator)
            case TokenType.STAR:
                return self._number(left, operator) * self._number(right, operator)
            case TokenType.SLASH:
                divisor = self._number(right, operator)
                if divisor == 0:
                    raise RuntimeError("Division by zero", operator)
                return self._number(left, operator) / divisor
            case TokenType.GREATER:
                return self._number(left, operator) > self._number(right, operator)
            case TokenType.GREATER_EQUAL:
                return self._number(left, operator) >= self._number(right, operator)
            case TokenType.LESS:
                return self._number(left, operator) < self._number(right, operator)
            case TokenType.LESS_EQUAL:
                return self._number(left, operator) <= self._number(right, operator)
            case TokenType.EQUAL_EQUAL:
                return left == right
            case TokenType.BANG_EQUAL:
                return left != right
            case TokenType.AND_AND:
                return self._truthy(left) and self._truthy(right)
            case TokenType.OR_OR:
                return self._truthy(left) or self._truthy(right)
        raise RuntimeError(f"Unsupported binary operator '{operator.lexeme}'", operator)

    @staticmethod
    def _truthy(value: Value) -> bool:
        return value is not False and value is not None

    @staticmethod
    def _number(value: Value, token: Token) -> float | int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError("Operand must be a number", token)
        return value

    @staticmethod
    def _display(value: Value) -> str:
        if isinstance(value, bool):
            return str(value).lower()
        return str(value)
