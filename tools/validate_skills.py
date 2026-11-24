#!/usr/bin/env python3
"""Validate every skill folder against the published Agent Skills format.

Rules checked (from the Agent Skills overview documentation):
  * SKILL.md exists and starts with YAML frontmatter
  * name: required, 64 characters or fewer, lowercase letters, numbers and
    hyphens only, no reserved words (anthropic, claude), matches the folder
  * description: required, non-empty, 1,024 characters or fewer, no XML tags
  * the body stays under 500 lines and every relative link resolves

Usage: python tools/validate_skills.py [skills_dir]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
XML_RE = re.compile(r"<[^>]+>")
RESERVED = ("anthropic", "claude")
MAX_BODY_LINES = 500


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the simple `key: value` frontmatter used by SKILL.md files."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with a --- frontmatter line")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        raise ValueError("frontmatter is not closed with ---") from None
    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"frontmatter line is not key: value -> {line!r}")
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, "\n".join(lines[end + 1:])


def validate_skill(skill_dir: Path) -> list[str]:
    problems: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir.name}: SKILL.md is missing"]
    try:
        meta, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{skill_dir.name}: {exc}"]

    name = meta.get("name", "")
    if not name:
        problems.append("name is required")
    else:
        if len(name) > 64:
            problems.append("name is longer than 64 characters")
        if not NAME_RE.match(name):
            problems.append("name must use lowercase letters, numbers and hyphens only")
        if any(word in name for word in RESERVED):
            problems.append("name contains a reserved word")
        if name != skill_dir.name:
            problems.append(f"name '{name}' does not match folder '{skill_dir.name}'")

    description = meta.get("description", "")
    if not description:
        problems.append("description is required")
    elif len(description) > 1024:
        problems.append("description is longer than 1,024 characters")
    if XML_RE.search(description) or XML_RE.search(name):
        problems.append("name and description cannot contain XML tags")

    if len(body.splitlines()) > MAX_BODY_LINES:
        problems.append(f"body is longer than {MAX_BODY_LINES} lines")
    for target in LINK_RE.findall(body):
        if re.match(r"^[a-z]+://|^#|^mailto:", target):
            continue
        if not (skill_dir / target.split("#")[0]).exists():
            problems.append(f"broken link: {target}")
    return [f"{skill_dir.name}: {p}" for p in problems]


def validate_all(skills_dir: Path) -> list[str]:
    folders = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    if not folders:
        return [f"no skill folders found in {skills_dir}"]
    return [problem for folder in folders for problem in validate_skill(folder)]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    skills_dir = Path(args[0]) if args else Path(__file__).resolve().parent.parent / "skills"
    problems = validate_all(skills_dir)
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        count = sum(1 for p in skills_dir.iterdir() if p.is_dir())
        print(f"OK {count} skill(s) pass the format checks")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
