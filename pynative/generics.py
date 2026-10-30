"""Type unification and lazy monomorphization for generic functions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ast_nodes import CallExpr, Expression, FunctionStmt, Program
from .semantic import (
    BOOL,
    FLOAT,
    INT,
    STRING,
    FunctionType,
    SemanticError,
    Type,
    UNKNOWN,
)
from .tokens import Token


@dataclass(frozen=True, slots=True)
class TypeVariable:
    """A first-order type variable used while solving generic constraints."""

    name: str


GenericType = Type | TypeVariable


@dataclass(frozen=True, slots=True)
class TypeScheme:
    """A generic function signature before its type variables are substituted."""

    parameters: tuple[GenericType, ...]
    return_type: GenericType


@dataclass(frozen=True, slots=True)
class Specialization:
    """One concrete instantiation of a generic function."""

    function: FunctionStmt
    type_arguments: tuple[Type, ...]
    name: str


@dataclass
class Monomorphizer:
    """Unify generic calls and cache one specialization per type tuple."""

    functions: dict[str, FunctionStmt]
    specializations: dict[tuple[str, tuple[Type, ...]], Specialization] = field(
        default_factory=dict
    )

    @classmethod
    def from_program(cls, program: Program) -> "Monomorphizer":
        return cls(
            {
                statement.name.lexeme: statement
                for statement in program.statements
                if isinstance(statement, FunctionStmt)
            }
        )

    def specialize(
        self, function_name: str, argument_types: tuple[Type, ...], token: Token
    ) -> Specialization:
        function = self.functions.get(function_name)
        if function is None:
            raise SemanticError(f"Unknown function '{function_name}'", token)
        if not function.type_parameters:
            raise SemanticError(
                f"Function '{function_name}' is not generic", token
            )
        if len(argument_types) != len(function.parameters):
            raise SemanticError(
                f"Expected {len(function.parameters)} arguments but got {len(argument_types)}",
                token,
            )
        key = (function_name, argument_types)
        existing = self.specializations.get(key)
        if existing is not None:
            return existing
        substitutions: dict[str, Type] = {}
        for parameter, argument, annotation in zip(
            function.parameters, argument_types, function.parameter_types
        ):
            if annotation is not None and annotation.lexeme in {
                item.lexeme for item in function.type_parameters
            }:
                previous = substitutions.setdefault(annotation.lexeme, argument)
                if previous != argument:
                    raise SemanticError(
                        f"Conflicting types for '{parameter.lexeme}'", parameter
                    )
        if len(substitutions) != len(function.type_parameters):
            raise SemanticError("Could not infer all generic type arguments", function.name)
        name = f"{function_name}_{'_'.join(type_info.name for type_info in argument_types)}"
        result = Specialization(function, argument_types, name)
        self.specializations[key] = result
        return result


def primitive_type(name: str) -> Type:
    """Resolve a source-level primitive type annotation."""

    try:
        return {"int": INT, "float": FLOAT, "bool": BOOL, "string": STRING}[name]
    except KeyError as error:
        raise ValueError(f"Unknown primitive type '{name}'") from error
