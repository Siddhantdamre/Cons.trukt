"""Compatibility wrapper for querying C-OS precedent memory."""

from __future__ import annotations

from cons_trukt.cli import main as cli_main


def ask_c_os(question: str = "common reasons for plan review rejection on steep slopes") -> int:
    return cli_main(["query", question])


if __name__ == "__main__":
    raise SystemExit(ask_c_os())
