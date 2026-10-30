"""Tree-walk evaluation for PyNative programs."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ast_nodes import (
    AssignStmt, BinaryExpr, BlockStmt, CallExpr, Expression, ExpressionStmt,
    FunctionStmt, GroupingExpr, IfStmt, LetStmt, LiteralExpr, PrintStmt,
    Program, ReturnStmt, Statement, UnaryExpr, VariableExpr,
)
from .tokens import Token, TokenType

Value = object


@dataclass(frozen=True, slots=True)
class RuntimeError(Exception):
    """A source-location-aware runtime error."""
    message: str
    token: Token

    def __str__(self) -> str:
        return f"{self.message} at line {self.token.line}, column {self.token.column}."


class ReturnSignal(Exception):
    """Internal control-flow signal used to exit a function call."""

    def __init__(self, value: Value) -> None:
        self.value = value


@dataclass(frozen=True, slots=True)
class UserFunction:
    """A callable function declared in a PyNative program."""
    declaration: FunctionStmt


@dataclass(slots=True)
class Interpreter:
    """Evaluate PyNative syntax trees using global and function-local scopes."""
    environment: dict[str, Value] = field(default_factory=dict)
    output: list[str] = field(default_factory=list)
    local_scopes: list[dict[str, Value]] = field(default_factory=list)

    def execute(self, program: Program) -> None:
        """Execute every statement in a program."""
        for statement in program.statements:
            self.execute_statement(statement)

    def execute_statement(self, statement: Statement) -> None:
        """Execute one statement."""
        match statement:
            case LetStmt(name, initializer):
                self._current_scope()[name.lexeme] = self.evaluate(initializer)
            case AssignStmt(name, value):
                self._assign(name, self.evaluate(value))
            case PrintStmt(expression):
                self.output.append(self._display(self.evaluate(expression)))
            case ExpressionStmt(expression):
                self.evaluate(expression)
            case BlockStmt(statements):
                for nested_statement in statements:
                    self.execute_statement(nested_statement)
            case IfStmt(condition, then_branch, else_branch):
                if self._truthy(self.evaluate(condition)):
                    self.execute_statement(then_branch)
                elif else_branch is not None:
                    self.execute_statement(else_branch)
            case FunctionStmt() as declaration:
                self._current_scope()[declaration.name.lexeme] = UserFunction(declaration)
            case ReturnStmt(keyword, value):
                if not self.local_scopes:
                    raise RuntimeError("Cannot return outside a function", keyword)
                raise ReturnSignal(None if value is None else self.evaluate(value))

    def evaluate(self, expression: Expression) -> Value:
        """Evaluate one expression and return its runtime value."""
        match expression:
            case LiteralExpr(value):
                return value
            case GroupingExpr(inner):
                return self.evaluate(inner)
            case VariableExpr(name):
                return self._lookup(name)
            case UnaryExpr(operator, right):
                return self._unary(operator, self.evaluate(right))
            case BinaryExpr(left, operator, right):
                return self._binary(operator, self.evaluate(left), self.evaluate(right))
            case CallExpr(callee, paren, arguments):
                function = self.evaluate(callee)
                if not isinstance(function, UserFunction):
                    raise RuntimeError("Can only call functions", paren)
                return self._call(function, [self.evaluate(argument) for argument in arguments], paren)

    def _call(self, function: UserFunction, arguments: list[Value], token: Token) -> Value:
        declaration = function.declaration
        if len(arguments) != len(declaration.parameters):
            raise RuntimeError(f"Expected {len(declaration.parameters)} arguments but got {len(arguments)}", token)
        scope = dict(zip((parameter.lexeme for parameter in declaration.parameters), arguments))
        self.local_scopes.append(scope)
        try:
            self.execute_statement(declaration.body)
        except ReturnSignal as signal:
            return signal.value
        finally:
            self.local_scopes.pop()
        return None

    def _current_scope(self) -> dict[str, Value]:
        return self.local_scopes[-1] if self.local_scopes else self.environment

    def _lookup(self, name: Token) -> Value:
        for scope in reversed(self.local_scopes):
            if name.lexeme in scope:
                return scope[name.lexeme]
        try:
            return self.environment[name.lexeme]
        except KeyError as error:
            raise RuntimeError(f"Undefined variable '{name.lexeme}'", name) from error

    def _assign(self, name: Token, value: Value) -> None:
        for scope in reversed(self.local_scopes):
            if name.lexeme in scope:
                scope[name.lexeme] = value
                return
        if name.lexeme in self.environment:
            self.environment[name.lexeme] = value
            return
        raise RuntimeError(f"Undefined variable '{name.lexeme}'", name)

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
        return str(value).lower() if isinstance(value, bool) else str(value)
