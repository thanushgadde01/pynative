"""Deterministic MLIR text lowering for the typed PyNative frontend."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ast_nodes import (
    BinaryExpr,
    BlockStmt,
    Expression,
    ExpressionStmt,
    FunctionStmt,
    GroupingExpr,
    IfStmt,
    LetStmt,
    LiteralExpr,
    PrintStmt,
    Program,
    ReturnStmt,
    Statement,
    UnaryExpr,
    VariableExpr,
)
from .semantic import FLOAT, INT, Type, TypedProgram, analyze
from .tokens import TokenType


@dataclass
class _Emitter:
    typed: TypedProgram
    lines: list[str] = field(default_factory=list)
    values: dict[str, str] = field(default_factory=dict)
    counter: int = 0

    def emit(self) -> str:
        self.lines.append("module {")
        for statement in self.typed.program.statements:
            if isinstance(statement, FunctionStmt):
                self._function(statement)
        self.lines.append("  func.func @main() -> i64 {")
        for statement in self.typed.program.statements:
            if not isinstance(statement, FunctionStmt):
                self._statement(statement)
        self.lines.append("    %result = arith.constant 0 : i64")
        self.lines.append("    return %result : i64")
        self.lines.append("  }")
        self.lines.append("}")
        return "\n".join(self.lines) + "\n"

    def _function(self, function: FunctionStmt) -> None:
        parameters = ", ".join(f"%arg{index}: i64" for index, _ in enumerate(function.parameters))
        self.lines.append(f"  func.func @{function.name.lexeme}({parameters}) -> i64 {{")
        self.lines.append("    %result = arith.constant 0 : i64")
        self.lines.append("    return %result : i64")
        self.lines.append("  }")

    def _statement(self, statement: Statement) -> None:
        match statement:
            case LetStmt(name, initializer):
                self.values[name.lexeme] = self._expression(initializer)
            case ExpressionStmt(expression) | PrintStmt(expression):
                self._expression(expression)
            case BlockStmt(statements):
                for nested in statements:
                    self._statement(nested)
            case IfStmt(condition, then_branch, else_branch):
                condition_value = self._expression(condition)
                self.lines.append(f"    scf.if {condition_value} {{")
                self._statement(then_branch)
                self.lines.append("    }")
                if else_branch is not None:
                    self.lines.append("    else {")
                    self._statement(else_branch)
                    self.lines.append("    }")
            case ReturnStmt():
                return

    def _expression(self, expression: Expression) -> str:
        if isinstance(expression, LiteralExpr):
            return self._constant(expression.value)
        if isinstance(expression, VariableExpr):
            return self.values.get(expression.name.lexeme, "%unknown")
        if isinstance(expression, GroupingExpr):
            return self._expression(expression.expression)
        if isinstance(expression, UnaryExpr):
            value = self._expression(expression.right)
            if expression.operator.type == TokenType.MINUS:
                result = self._new_value()
                self.lines.append(f"    {result} = arith.negf {value} : f64")
                return result
            return value
        if isinstance(expression, BinaryExpr):
            left = self._expression(expression.left)
            right = self._expression(expression.right)
            result = self._new_value()
            operation = {
                TokenType.PLUS: "addi",
                TokenType.MINUS: "subi",
                TokenType.STAR: "muli",
            }.get(expression.operator.type)
            if operation is None:
                return left
            self.lines.append(f"    {result} = arith.{operation} {left}, {right} : i64")
            return result
        return "%unknown"

    def _constant(self, value: object) -> str:
        result = self._new_value()
        if isinstance(value, bool):
            literal = "1" if value else "0"
            self.lines.append(f"    {result} = arith.constant {literal} : i1")
        elif isinstance(value, int):
            self.lines.append(f"    {result} = arith.constant {value} : i64")
        elif isinstance(value, float):
            self.lines.append(f"    {result} = arith.constant {value} : f64")
        else:
            self.lines.append(f"    {result} = arith.constant 0 : i64")
        return result

    def _new_value(self) -> str:
        value = f"%v{self.counter}"
        self.counter += 1
        return value


def lower_to_mlir(program: Program | TypedProgram) -> str:
    """Lower a parsed or analyzed program to deterministic MLIR text."""

    typed = program if isinstance(program, TypedProgram) else analyze(program)
    return _Emitter(typed).emit()
