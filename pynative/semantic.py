"""Semantic analysis and primitive type inference for PyNative programs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from .ast_nodes import (
    AssignStmt,
    BinaryExpr,
    BlockStmt,
    CallExpr,
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
from .tokens import Token, TokenType


@dataclass(frozen=True, slots=True)
class Type:
    """A named language type."""

    name: str

    def __str__(self) -> str:
        return self.name


INT = Type("int")
FLOAT = Type("float")
BOOL = Type("bool")
STRING = Type("string")
UNKNOWN = Type("unknown")
VOID = Type("void")


@dataclass(frozen=True, slots=True)
class FunctionType:
    """The parameter and return types known for a function declaration."""

    parameters: tuple[Type, ...]
    return_type: Type


TypeInfo: TypeAlias = Type | FunctionType


@dataclass(frozen=True, slots=True)
class Symbol:
    """A resolved declaration in a lexical scope."""

    name: str
    type: TypeInfo
    token: Token


@dataclass(frozen=True, slots=True)
class SemanticError(Exception):
    """A source-location-aware static semantic error."""

    message: str
    token: Token

    def __str__(self) -> str:
        return f"{self.message} at line {self.token.line}, column {self.token.column}."


@dataclass(frozen=True, slots=True)
class TypedProgram:
    """A source program with inferred types attached by node identity."""

    program: Program
    expression_types: dict[Expression, TypeInfo]
    declaration_types: dict[Statement, TypeInfo]


@dataclass
class _Analyzer:
    expression_types: dict[Expression, TypeInfo] = field(default_factory=dict)
    declaration_types: dict[Statement, TypeInfo] = field(default_factory=dict)
    scopes: list[dict[str, Symbol]] = field(default_factory=lambda: [{}])
    current_function: list[FunctionType] = field(default_factory=list)
    return_types: list[list[Type]] = field(default_factory=list)

    def analyze(self, program: Program) -> TypedProgram:
        self._declare_functions(program.statements)
        for statement in program.statements:
            self._statement(statement)
        return TypedProgram(program, self.expression_types, self.declaration_types)

    def _declare_functions(self, statements: tuple[Statement, ...]) -> None:
        for statement in statements:
            if isinstance(statement, FunctionStmt):
                function_type = FunctionType(
                    (UNKNOWN,) * len(statement.parameters), UNKNOWN
                )
                self._declare(statement.name, function_type)
                self.declaration_types[statement] = function_type

    def _statement(self, statement: Statement) -> None:
        match statement:
            case LetStmt(name, initializer):
                value_type = self._expression(initializer)
                self._declare(name, value_type)
                self.declaration_types[statement] = value_type
            case AssignStmt(name, value):
                symbol = self._lookup(name)
                if isinstance(symbol.type, FunctionType):
                    self._error("Cannot assign to a function", name)
                self._require_compatible(symbol.type, self._expression(value), name)
            case PrintStmt(expression) | ExpressionStmt(expression):
                self._expression(expression)
            case BlockStmt(statements):
                self._block(statements)
            case IfStmt(condition, then_branch, else_branch):
                self._require_type(BOOL, self._expression(condition), condition)
                self._statement(then_branch)
                if else_branch is not None:
                    self._statement(else_branch)
            case FunctionStmt() as declaration:
                self._function(declaration)
            case ReturnStmt(keyword, value):
                if not self.current_function:
                    self._error("Cannot return outside a function", keyword)
                return_type = VOID if value is None else self._expression(value)
                self.return_types[-1].append(return_type)
                self._require_compatible(self.current_function[-1].return_type, return_type, keyword)

    def _function(self, declaration: FunctionStmt) -> None:
        symbol = self._lookup(declaration.name)
        assert isinstance(symbol.type, FunctionType)
        function_type = symbol.type
        self.scopes.append({})
        self.current_function.append(function_type)
        self.return_types.append([])
        try:
            for parameter, parameter_type in zip(declaration.parameters, function_type.parameters):
                self._declare(parameter, parameter_type)
            self._declare_functions(declaration.body.statements)
            self._block_contents(declaration.body.statements)
            inferred_return = self._merge_types(self.return_types[-1])
            updated = FunctionType(function_type.parameters, inferred_return)
            self._replace_symbol(declaration.name, updated)
            self.declaration_types[declaration] = updated
        finally:
            self.return_types.pop()
            self.current_function.pop()
            self.scopes.pop()

    def _block(self, statements: tuple[Statement, ...]) -> None:
        self.scopes.append({})
        try:
            self._declare_functions(statements)
            self._block_contents(statements)
        finally:
            self.scopes.pop()

    def _block_contents(self, statements: tuple[Statement, ...]) -> None:
        for statement in statements:
            self._statement(statement)

    def _expression(self, expression: Expression) -> TypeInfo:
        if expression in self.expression_types:
            return self.expression_types[expression]
        match expression:
            case LiteralExpr(value):
                result = BOOL if isinstance(value, bool) else (
                    INT if isinstance(value, int) else FLOAT if isinstance(value, float) else STRING
                )
            case GroupingExpr(inner):
                result = self._expression(inner)
            case VariableExpr(name):
                result = self._lookup(name).type
            case UnaryExpr(operator, right):
                right_type = self._expression(right)
                if operator.type == TokenType.BANG:
                    result = BOOL
                else:
                    self._require_numeric(right_type, operator)
                    result = right_type
            case BinaryExpr(left, operator, right):
                result = self._binary(operator, self._expression(left), self._expression(right))
            case CallExpr(callee, paren, arguments):
                function = self._expression(callee)
                if not isinstance(function, FunctionType):
                    self._error("Can only call functions", paren)
                if len(arguments) != len(function.parameters):
                    self._error(
                        f"Expected {len(function.parameters)} arguments but got {len(arguments)}",
                        paren,
                    )
                for expected, argument in zip(function.parameters, arguments):
                    self._require_compatible(expected, self._expression(argument), paren)
                result = function.return_type
            case _:
                raise AssertionError(f"Unhandled expression: {expression!r}")
        self.expression_types[expression] = result
        return result

    def _binary(self, operator: Token, left: TypeInfo, right: TypeInfo) -> Type:
        if operator.type in (TokenType.AND_AND, TokenType.OR_OR):
            return BOOL
        if operator.type in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            return BOOL
        if operator.type == TokenType.PLUS and (left == STRING or right == STRING):
            return STRING
        self._require_numeric(left, operator)
        self._require_numeric(right, operator)
        if operator.type in (
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            return BOOL
        return FLOAT if FLOAT in (left, right) or operator.type == TokenType.SLASH else INT

    def _lookup(self, token: Token) -> Symbol:
        for scope in reversed(self.scopes):
            if token.lexeme in scope:
                return scope[token.lexeme]
        self._error(f"Undefined variable '{token.lexeme}'", token)

    def _declare(self, token: Token, type_info: TypeInfo) -> None:
        scope = self.scopes[-1]
        if token.lexeme in scope:
            self._error(f"Already declared '{token.lexeme}'", token)
        scope[token.lexeme] = Symbol(token.lexeme, type_info, token)

    def _replace_symbol(self, token: Token, type_info: TypeInfo) -> None:
        for scope in reversed(self.scopes):
            if token.lexeme in scope:
                symbol = scope[token.lexeme]
                scope[token.lexeme] = Symbol(symbol.name, type_info, symbol.token)
                return

    def _require_numeric(self, type_info: TypeInfo, token: Token) -> None:
        if type_info not in (INT, FLOAT, UNKNOWN):
            self._error("Operand must be a number", token)

    def _require_type(self, expected: Type, actual: TypeInfo, expression: Expression) -> None:
        if actual not in (expected, UNKNOWN):
            token = self._expression_token(expression)
            self._error(f"Expected {expected} but got {actual}", token)

    def _require_compatible(self, expected: TypeInfo, actual: TypeInfo, token: Token) -> None:
        if expected != UNKNOWN and actual != UNKNOWN and expected != actual:
            self._error(f"Expected {expected} but got {actual}", token)

    @staticmethod
    def _merge_types(types: list[Type]) -> Type:
        if not types:
            return VOID
        result = types[0]
        for type_info in types[1:]:
            if result == UNKNOWN:
                result = type_info
            elif type_info != UNKNOWN and type_info != result:
                return UNKNOWN
        return result

    @staticmethod
    def _expression_token(expression: Expression) -> Token:
        if isinstance(expression, VariableExpr):
            return expression.name
        if isinstance(expression, (UnaryExpr, BinaryExpr)):
            return expression.operator
        if isinstance(expression, CallExpr):
            return expression.paren
        return Token(TokenType.EOF, "", None, 0, 0)

    @staticmethod
    def _error(message: str, token: Token) -> None:
        raise SemanticError(message, token)


def analyze(program: Program) -> TypedProgram:
    """Resolve names and infer primitive types for a parsed program."""

    return _Analyzer().analyze(program)
