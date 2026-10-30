# PyNative

PyNative is a minimal tree-walk interpreter for a small C-like language.

## Days 1–2: Lexer and expression parser

The first milestone provides a typed, location-aware lexer for the C-like v0.1
syntax. It supports identifiers, integers and floats, strings with common
escapes, language keywords, punctuation, arithmetic/comparison/boolean
operators, and `#` or `//` line comments.

Run the tests:

```powershell
python -m pytest
```

Inspect a source file's tokens:

```powershell
python -m pynative.cli --tokens .\examples\lexer_demo.pyn
```

Day 2 adds a recursive-descent parser for expressions. It handles parentheses,
unary `!`/`-`, arithmetic, comparisons, equality, and `&&`/`||` with
conventional precedence and left associativity.

Print an expression AST in prefix notation:

```powershell
python -m pynative.cli --ast .\examples\expression.pyn
```

## Day 3: Expression evaluation

The tree-walk interpreter now evaluates literals, grouping, unary expressions,
arithmetic, comparisons, equality, boolean operations, and string
concatenation. It detects undefined variables, invalid numeric operands, and
division by zero with source locations.

## Day 4: Variables and simple statements

Programs now support `let name = expression;`, reassignment, expression
statements, and `print(expression);`. A program uses one global environment;
assigning an undeclared variable is a runtime error.

## Day 5: Conditional control flow

The language now supports `if (condition) statement` with optional `else`
branches and brace-delimited blocks. Conditions use the interpreter's boolean
truthiness rules.

## Day 6: Functions and returns

The interpreter supports named functions, parameters, calls, local parameter
scopes, recursion, and `return`. Function calls validate argument counts.

## Day 7: Script runner and capstone

The CLI now runs complete `.pyn` programs by default. The capstone program
demonstrates variables, functions, recursion, conditionals, arithmetic, and
output:

```powershell
python -m pynative.cli .\examples\capstone.pyn
```

Expected output:

```text
Sum is: 15
```

Use `--tokens` to inspect lexical output or `--ast` for a single expression.
All components are covered by the test suite:

```powershell
python -m pytest
```

## Progress / Implementation Status

- [x] **Phase 1: Frontend & Typed AST** — Added `pynative.semantic` with
  lexical-scope symbol resolution, primitive type inference, function
  signatures, return checking, and source-location-aware semantic errors.
  `TypedProgram` keeps inferred expression and declaration types alongside the
  existing AST, so the interpreter remains compatible while compiler work
  begins.
- [x] **Phase 1 validation** — Arithmetic, conditionals, functions, string
  concatenation, invalid operands, and invalid conditions are covered by
  semantic tests; the complete suite passes with **33 tests passed**.
- [x] **Phase 2: Type Inference & Generics** — Added generic function and
  primitive type-annotation syntax, first-order type variables, and a lazy
  specialization cache that produces stable names such as `id_int` and
  `id_string`. Existing untyped function syntax remains valid.
- [x] **Phase 3: MLIR Lowering** — Added deterministic MLIR text emission from
  the typed AST with `func`, `arith`, and `scf` structure, stable SSA names,
  primitive constants, arithmetic, functions, and conditionals. The backend
  has no runtime dependency; `mlir-opt` can be used externally when installed
  (not available in this environment).
- [x] **Phase 4: LLVM & Native Code Generation** — Added LLVM IR emission for
  the initial integer subset and `compile_native`, which writes `.ll`, invokes
  `clang -O3`, and surfaces unavailable-toolchain or compiler errors explicitly.
  Native compilation remains optional because this Windows environment has no
  `clang` installed.
- [ ] **Phase 5: Optimization & Final Features** — Add optimization controls,
  deterministic resource-management hooks, benchmarking, and CI coverage.

The current frontend intentionally uses an internal `unknown` type for
unannotated function parameters because the Day 7 grammar has no type
annotation syntax. Known primitive expressions are checked statically, while
the existing interpreter and language syntax remain unchanged.
