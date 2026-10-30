"""Small deterministic optimization and resource-management utilities."""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, replace
from time import perf_counter
from typing import Callable, Generic, TypeVar

from .ast_nodes import BinaryExpr, Expression, LetStmt, LiteralExpr, Program, Statement
from .tokens import TokenType

T = TypeVar("T")


def optimize(program: Program) -> Program:
    """Fold safe integer arithmetic while preserving the source AST shape."""

    return replace(
        program,
        statements=tuple(_statement(statement) for statement in program.statements),
    )


def _statement(statement: Statement) -> Statement:
    if isinstance(statement, LetStmt):
        return replace(statement, initializer=_expression(statement.initializer))
    return statement


def _expression(expression: Expression) -> Expression:
    if isinstance(expression, BinaryExpr):
        left = _expression(expression.left)
        right = _expression(expression.right)
        if (
            isinstance(left, LiteralExpr)
            and isinstance(right, LiteralExpr)
            and isinstance(left.value, int)
            and not isinstance(left.value, bool)
            and isinstance(right.value, int)
            and not isinstance(right.value, bool)
        ):
            operations = {
                TokenType.PLUS: lambda: left.value + right.value,
                TokenType.MINUS: lambda: left.value - right.value,
                TokenType.STAR: lambda: left.value * right.value,
            }
            operation = operations.get(expression.operator.type)
            if operation is not None:
                return LiteralExpr(operation())
        return replace(expression, left=left, right=right)
    return expression


@dataclass
class Arena(AbstractContextManager["Arena"]):
    """A deterministic region that closes registered resources as a group."""

    resources: list[Callable[[], None]]

    def __init__(self) -> None:
        self.resources = []

    def register(self, cleanup: Callable[[], None]) -> None:
        self.resources.append(cleanup)

    def close(self) -> None:
        while self.resources:
            self.resources.pop()()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def benchmark(function: Callable[[], T], iterations: int = 1) -> tuple[T, float]:
    """Run a callable repeatedly and return its last value and elapsed seconds."""

    if iterations < 1:
        raise ValueError("iterations must be positive")
    start = perf_counter()
    value: T | None = None
    for _ in range(iterations):
        value = function()
    return value, perf_counter() - start
