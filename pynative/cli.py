"""Command-line entry point for inspecting PyNative source tokens."""

from __future__ import annotations

import argparse
from pathlib import Path

from .lexer import Lexer, LexerError
from .parser import ParseError, Parser


def main() -> int:
    """Tokenize a source file and print one token per line."""
    parser = argparse.ArgumentParser(description="Inspect a PyNative expression.")
    parser.add_argument("source", type=Path, help="Path to the source file")
    parser.add_argument("--ast", action="store_true", help="Print the parsed expression tree")
    arguments = parser.parse_args()

    try:
        source = arguments.source.read_text(encoding="utf-8")
        tokens = Lexer(source).scan_tokens()
    except OSError as error:
        parser.error(str(error))
    except LexerError as error:
        parser.error(str(error))

    if arguments.ast:
        try:
            from .ast_printer import format_expression

            print(format_expression(Parser(tokens).parse_expression()))
            return 0
        except ParseError as error:
            parser.error(str(error))

    for token in tokens:
        print(f"{token.line}:{token.column}\t{token.type.name}\t{token.lexeme!r}\t{token.literal!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
