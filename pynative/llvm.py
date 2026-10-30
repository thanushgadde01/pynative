"""Minimal LLVM IR emission and native toolchain integration."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .ast_nodes import BinaryExpr, Expression, LetStmt, LiteralExpr, Program
from .semantic import analyze
from .tokens import TokenType


class ToolchainError(RuntimeError):
    """The requested native compiler is unavailable or failed."""


def lower_to_llvm_ir(program: Program) -> str:
    """Emit LLVM IR for integer literals, additions, and the main function."""

    analyze(program)
    lines = [
        '; ModuleID = "pynative"',
        'target triple = "unknown-unknown-unknown"',
        "",
        "define i64 @main() {",
        "entry:",
    ]
    next_value = 0
    names: dict[str, str] = {}
    for statement in program.statements:
        if isinstance(statement, LetStmt):
            value, next_value = _expression(statement.initializer, names, lines, next_value)
            names[statement.name.lexeme] = value
    lines.extend(["  ret i64 0", "}"])
    return "\n".join(lines) + "\n"


def compile_native(program: Program, output: Path) -> Path:
    """Compile LLVM IR to a native executable using clang."""

    clang = shutil.which("clang")
    if clang is None:
        raise ToolchainError("clang is required for native compilation but was not found")
    ir_path = output.with_suffix(".ll")
    ir_path.write_text(lower_to_llvm_ir(program), encoding="utf-8")
    completed = subprocess.run(
        [clang, str(ir_path), "-O3", "-o", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ToolchainError(completed.stderr.strip() or "clang failed")
    return output


def _expression(
    expression: Expression,
    names: dict[str, str],
    lines: list[str],
    next_value: int,
) -> tuple[str, int]:
    if isinstance(expression, LiteralExpr) and isinstance(expression.value, int):
        return str(expression.value), next_value
    if isinstance(expression, BinaryExpr) and expression.operator.type == TokenType.PLUS:
        left, next_value = _expression(expression.left, names, lines, next_value)
        right, next_value = _expression(expression.right, names, lines, next_value)
        result = f"%v{next_value}"
        lines.append(f"  {result} = add i64 {left}, {right}")
        return result, next_value + 1
    if hasattr(expression, "name"):
        return names.get(expression.name.lexeme, "0"), next_value
    return "0", next_value
