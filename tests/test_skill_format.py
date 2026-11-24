from pathlib import Path

import pytest

import validate_skills

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".md", ".py", ".json", ".yml", ".txt", ".example", ""}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", ".deps"}


def make_skill(tmp_path, folder, frontmatter, body="# Title\n"):
    skill = tmp_path / folder
    skill.mkdir()
    (skill / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return skill


def test_all_shipped_skills_are_valid():
    assert validate_skills.validate_all(ROOT / "skills") == []
    assert len(list((ROOT / "skills").glob("*/SKILL.md"))) == 3


def test_every_skill_ships_a_script_a_reference_and_an_example():
    for skill in (ROOT / "skills").iterdir():
        for part in ("scripts/*.py", "references/*.md", "examples/*"):
            assert list(skill.glob(part)), f"{skill.name} has no {part}"


@pytest.mark.parametrize("folder, frontmatter, expected", [
    ("Bad_Name", "name: Bad_Name\ndescription: x", "lowercase"),
    ("claude-helper", "name: claude-helper\ndescription: x", "reserved"),
    ("one", "name: two\ndescription: x", "does not match folder"),
    ("no-desc", "name: no-desc", "description is required"),
    ("long-desc", "name: long-desc\ndescription: " + "x" * 1025, "1,024"),
    ("xml-desc", "name: xml-desc\ndescription: use <b>this</b>", "XML"),
    ("n" * 65, "name: " + "n" * 65 + "\ndescription: x", "64 characters"),
])
def test_format_rules_are_enforced(tmp_path, folder, frontmatter, expected):
    problems = validate_skills.validate_skill(make_skill(tmp_path, folder, frontmatter))
    assert any(expected in p for p in problems), problems


def test_broken_link_and_missing_frontmatter(tmp_path):
    skill = make_skill(tmp_path, "linky", "name: linky\ndescription: x", "See [ref](references/none.md)\n")
    assert any("broken link" in p for p in validate_skills.validate_skill(skill))
    (skill / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    assert any("frontmatter" in p for p in validate_skills.validate_skill(skill))


def test_repo_has_no_em_dashes():
    offenders = []
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and not SKIP_DIRS & set(path.parts):
            if chr(0x2014) in path.read_text(encoding="utf-8", errors="ignore"):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
