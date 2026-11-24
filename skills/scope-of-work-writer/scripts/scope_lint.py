#!/usr/bin/env python3
"""Lint a scope of work draft (markdown) for the gaps that cause disputes.

Standard library only. Checks:
  * every required section heading is present
  * no vague phrases ("as needed", "etc", "TBD" and similar)
  * every bullet under Allowances carries a dollar amount
  * percentages under Payment schedule add up to 100

Usage:
    python scope_lint.py scope.md          # text findings, exit 1 on errors
    python scope_lint.py scope.md --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys

REQUIRED_SECTIONS = [
    "project summary", "inclusions", "exclusions", "allowances",
    "assumptions", "schedule", "payment schedule", "change process",
]
VAGUE_PHRASES = [
    r"\bas needed\b", r"\bas required\b", r"\betc\b\.?", r"\btbd\b", r"\bto be determined\b",
    r"\bmiscellaneous\b", r"\bmisc\b\.?", r"\bstandard grade\b", r"\band so on\b", r"\bif necessary\b",
]
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
MONEY = re.compile(r"\$\s?\d")
PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def split_sections(text: str) -> dict[str, list[tuple[int, str]]]:
    """Map lower-cased heading text to its (line number, line) body rows."""
    sections: dict[str, list[tuple[int, str]]] = {}
    current = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = HEADING.match(line)
        if match:
            current = match.group(1).strip().lower()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append((number, line))
    return sections


def lint(text: str) -> list[dict]:
    findings: list[dict] = []

    def add(level: str, code: str, message: str, line: int | None = None) -> None:
        findings.append({"level": level, "code": code, "message": message, "line": line})

    sections = split_sections(text)
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            add("error", "missing-section", f"Missing required section: {name.title()}")
        elif not any(row.strip() for _, row in sections[name]):
            add("error", "empty-section", f"Section is empty: {name.title()}")

    for number, line in enumerate(text.splitlines(), start=1):
        for pattern in VAGUE_PHRASES:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                add("warning", "vague-phrase", f"Vague phrase '{match.group(0)}': say exactly what is included", number)

    for number, line in sections.get("allowances", []):
        if BULLET.match(line) and not MONEY.search(line):
            add("error", "allowance-no-amount", "Allowance has no dollar amount", number)

    payment = sections.get("payment schedule")
    if payment:
        percents = [float(p) for _, line in payment for p in PERCENT.findall(line)]
        if not percents:
            add("warning", "payment-no-percent", "Payment schedule lists no percentages")
        elif abs(sum(percents) - 100.0) > 0.005:
            add("error", "payment-sum", f"Payment schedule adds up to {sum(percents):g}%, not 100%")
    return findings


def has_errors(findings: list[dict]) -> bool:
    return any(f["level"] == "error" for f in findings)


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "scope lint: clean, 0 findings"
    rows = []
    for f in findings:
        where = f"line {f['line']}: " if f["line"] else ""
        rows.append(f"{f['level'].upper():<8}{f['code']:<22}{where}{f['message']}")
    errors = sum(f["level"] == "error" for f in findings)
    rows.append(f"scope lint: {errors} error(s), {len(findings) - errors} warning(s)")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint a scope of work markdown draft.")
    parser.add_argument("scope_md", help="path to the scope of work draft")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)
    try:
        with open(args.scope_md, encoding="utf-8") as handle:
            findings = lint(handle.read())
    except OSError as exc:
        print(f"scope lint error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(findings, indent=2) if args.json else format_findings(findings))
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    sys.exit(main())
