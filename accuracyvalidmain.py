"""Compatibility wrapper for the legacy accuracy-focused pipeline entrypoint."""

from __future__ import annotations

from cons_trukt.cli import main as cli_main


def run_proper_c_os(filename: str = "plan.pdf") -> int:
    return cli_main(["run", "--input", filename])


if __name__ == "__main__":
    raise SystemExit(run_proper_c_os("plan.pdf"))
