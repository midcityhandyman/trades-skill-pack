from pathlib import Path

import scope_lint

EXAMPLES = Path(__file__).resolve().parent.parent / "skills/scope-of-work-writer/examples"


def codes(findings):
    return [f["code"] for f in findings]


def test_sample_scope_is_clean():
    assert scope_lint.lint((EXAMPLES / "sample_scope.md").read_text(encoding="utf-8")) == []


def test_flawed_scope_findings():
    findings = scope_lint.lint((EXAMPLES / "flawed_scope.md").read_text(encoding="utf-8"))
    missing = sorted(f["message"] for f in findings if f["code"] == "missing-section")
    assert missing == [
        "Missing required section: Assumptions",
        "Missing required section: Change Process",
        "Missing required section: Exclusions",
    ]
    assert codes(findings).count("vague-phrase") == 3
    assert codes(findings).count("allowance-no-amount") == 1
    assert any(f["code"] == "payment-sum" and "90%" in f["message"] for f in findings)
    assert scope_lint.has_errors(findings)


def test_vague_phrase_reports_line_number_and_is_only_a_warning():
    text = (EXAMPLES / "sample_scope.md").read_text(encoding="utf-8")
    text = text.replace("- Permits and permit fees", "- Permits if necessary")
    findings = scope_lint.lint(text)
    assert codes(findings) == ["vague-phrase"]
    assert text.splitlines()[findings[0]["line"] - 1] == "- Permits if necessary"
    assert not scope_lint.has_errors(findings)


def test_empty_section_is_an_error():
    text = (EXAMPLES / "sample_scope.md").read_text(encoding="utf-8")
    start, end = text.index("## Exclusions"), text.index("## Allowances")
    findings = scope_lint.lint(text[:start] + "## Exclusions\n\n" + text[end:])
    assert codes(findings) == ["empty-section"]


def test_headings_match_any_level_and_case():
    sections = scope_lint.split_sections("### PAYMENT SCHEDULE ###\n- Deposit: 100%\n")
    assert list(sections) == ["payment schedule"]


def test_cli_exit_codes(capsys, tmp_path):
    assert scope_lint.main([str(EXAMPLES / "sample_scope.md")]) == 0
    assert "clean, 0 findings" in capsys.readouterr().out
    assert scope_lint.main([str(EXAMPLES / "flawed_scope.md")]) == 1
    assert "error(s)" in capsys.readouterr().out
    assert scope_lint.main([str(tmp_path / "missing.md")]) == 2


def test_subheadings_stay_inside_their_section():
    text = (EXAMPLES / "sample_scope.md").read_text(encoding="utf-8")
    nested = text.replace("## Inclusions\n", "## Inclusions\n### Finishes\n")
    assert scope_lint.lint(nested) == []
    nested = text.replace("## Allowances\n", "## Allowances\n### Fixtures\n- Mirror: owner to choose\n")
    assert codes(scope_lint.lint(nested)) == ["allowance-no-amount"]
    nested = text.replace("- At completion walk through: 30%", "### Final\n- At completion walk through: 20%")
    assert codes(scope_lint.lint(nested)) == ["payment-sum"]
