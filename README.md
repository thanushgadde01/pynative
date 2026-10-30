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
