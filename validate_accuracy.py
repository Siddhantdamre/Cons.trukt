"""Compatibility wrapper for rule-based output audits."""

from __future__ import annotations

from cons_trukt.cli import main as cli_main


def run_accuracy_audit(limit: int = 10) -> int:
    return cli_main(["audit", "--limit", str(limit)])


if __name__ == "__main__":
    raise SystemExit(run_accuracy_audit())
