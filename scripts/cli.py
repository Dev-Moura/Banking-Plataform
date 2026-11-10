"""Dispatcher de comandos: format, lint, test, task, reconcile e seed."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence


def _run(command: Sequence[str]) -> int:
    print(f"$ {' '.join(command)}", flush=True)
    result = subprocess.run(command, check=False)
    return result.returncode


def format_cmd() -> None:
    """Formata o código com Ruff."""
    sys.exit(_run([sys.executable, "-m", "ruff", "format", "."]))


def lint_cmd() -> None:
    """Executa o lint com Ruff."""
    sys.exit(_run([sys.executable, "-m", "ruff", "check", "."]))


def test_cmd() -> None:
    """Executa a suíte de testes com cobertura."""
    sys.exit(
        _run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=banking",
                "--cov-report=term-missing",
            ]
        )
    )


def task_cmd() -> None:
    """Pipeline local completa: format check, lint e testes."""
    steps = [
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "-m", "ruff", "check", "."],
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=banking",
            "--cov-report=term-missing",
        ],
    ]
    for step in steps:
        code = _run(step)
        if code != 0:
            sys.exit(code)
    sys.exit(0)


def reconcile_cmd() -> None:
    """Executa a reconciliação entre saldos e lançamentos do ledger."""
    from scripts.reconcile import main as reconcile_main

    sys.exit(reconcile_main())


def seed_cmd() -> None:
    """Cria dados de demonstração financiados por conta sistêmica."""
    from scripts.seed import main as seed_main

    sys.exit(seed_main())


if __name__ == "__main__":
    task_cmd()
