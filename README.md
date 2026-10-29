# PyNative

PyNative is a minimal tree-walk interpreter, built incrementally.

## Day 1: Lexer

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
python -m pynative.cli .\example.pyn
```
