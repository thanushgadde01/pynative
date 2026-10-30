"""End-to-end tests for the Day 7 command-line script runner."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_cli_runs_capstone_program() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pynative.cli", "examples/capstone.pyn"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == "Sum is: 15\n"


def test_cli_can_print_tokens() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pynative.cli", "--tokens", "examples/expression.pyn"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "NUMBER" in result.stdout
