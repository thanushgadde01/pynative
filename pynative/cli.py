"""Command-line entry point for running and inspecting PyNative source."""

from __future__ import annotations

import argparse
from pathlib import Path

from .interpreter import Interpreter, RuntimeError
from .lexer import Lexer, LexerError
from .parser import ParseError, Parser


def main() -> int:
    """Run a source program, or inspect its tokens or expression tree."""
    parser = argparse.ArgumentParser(description="Run or inspect a PyNative source file.")
    parser.add_argument("source", type=Path, help="Path to the source file")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tokens", action="store_true", help="Print lexical tokens")
    mode.add_argument("--ast", action="store_true", help="Print a parsed expression tree")
    arguments = parser.parse_args()

    try:
        source = arguments.source.read_text(encoding="utf-8")
        tokens = Lexer(source).scan_tokens()
    except OSError as error:
        parser.error(str(error))
    except LexerError as error:
        parser.error(str(error))

    if arguments.tokens:
        for token in tokens:
            print(f"{token.line}:{token.column}\t{token.type.name}\t{token.lexeme!r}\t{token.literal!r}")
        return 0

    if arguments.ast:
        try:
            from .ast_printer import format_expression

            print(format_expression(Parser(tokens).parse_expression()))
            return 0
        except ParseError as error:
            parser.error(str(error))

    try:
        interpreter = Interpreter()
        interpreter.execute(Parser(tokens).parse_program())
    except (ParseError, RuntimeError) as error:
        parser.error(str(error))
    for line in interpreter.output:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
