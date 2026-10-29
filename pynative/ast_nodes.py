"""Abstract syntax tree nodes for PyNative expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .tokens import Token


@dataclass(frozen=True, slots=True)
class LiteralExpr:
    """A literal value such as a number, string, or boolean."""

    value: object


@dataclass(frozen=True, slots=True)
class VariableExpr:
    """A reference to a named variable."""

    name: Token


@dataclass(frozen=True, slots=True)
class GroupingExpr:
    """An expression enclosed in parentheses."""

    expression: Expression


@dataclass(frozen=True, slots=True)
class UnaryExpr:
    """A prefix operation, such as negation or logical not."""

    operator: Token
    right: Expression


@dataclass(frozen=True, slots=True)
class BinaryExpr:
    """An infix operation between two expressions."""

    left: Expression
    operator: Token
    right: Expression


Expression: TypeAlias = LiteralExpr | VariableExpr | GroupingExpr | UnaryExpr | BinaryExpr
