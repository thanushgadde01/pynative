"""Stable, compact formatting for expression trees."""

from .ast_nodes import BinaryExpr, Expression, GroupingExpr, LiteralExpr, UnaryExpr, VariableExpr


def format_expression(expression: Expression) -> str:
    """Render an expression in parenthesized prefix notation."""
    match expression:
        case LiteralExpr(value):
            return str(value).lower() if isinstance(value, bool) else repr(value)
        case VariableExpr(name):
            return name.lexeme
        case GroupingExpr(inner):
            return f"(group {format_expression(inner)})"
        case UnaryExpr(operator, right):
            return f"({operator.lexeme} {format_expression(right)})"
        case BinaryExpr(left, operator, right):
            return f"({operator.lexeme} {format_expression(left)} {format_expression(right)})"
