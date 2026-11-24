import copy
import json
from pathlib import Path

import pytest

import change_order

SAMPLE = Path(__file__).resolve().parent.parent / "skills/change-order-writer/examples/sample.json"


@pytest.fixture
def sample():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def test_sample_totals(sample):
    result = change_order.compute(sample)
    assert result["material_net"] == "50.00"
    assert result["labor_net"] == "420.00"
    assert result["subtotal"] == "470.00"
    assert result["markup"] == "70.50"
    assert result["material_tax"] == "4.00"
    assert result["change_total"] == "544.50"
    assert result["revised_contract_sum"] == "19494.50"


def test_net_credit_gets_no_markup_or_tax(sample):
    sample["items"] = [{"description": "Delete towel bar", "type": "credit", "category": "material",
                        "quantity": 2, "unit": "ea", "unit_price": "25.00"}]
    result = change_order.compute(sample)
    assert result["markup"] == "0.00"
    assert result["material_tax"] == "0.00"
    assert result["change_total"] == "-50.00"
    assert result["revised_contract_sum"] == "18900.00"


def test_tax_skipped_when_material_is_net_credit_but_labor_added(sample):
    sample["items"] = [
        {"description": "Credit tile", "type": "credit", "category": "material", "quantity": 1, "unit_price": 100},
        {"description": "Extra labor", "type": "add", "category": "labor", "quantity": 4, "unit_price": 50},
    ]
    result = change_order.compute(sample)
    assert result["material_tax"] == "0.00"
    assert result["markup"] == "15.00"
    assert result["change_total"] == "115.00"


def test_rounding_is_half_up_not_float(sample):
    sample.update(markup_pct=0, material_tax_pct=0)
    sample["items"] = [{"description": "x", "type": "add", "category": "labor",
                        "quantity": "0.5", "unit_price": "0.01"}]
    assert change_order.compute(sample)["change_total"] == "0.01"
    sample["items"][0].update(quantity=3, unit_price="0.1")
    assert change_order.compute(sample)["change_total"] == "0.30"


@pytest.mark.parametrize("mutate", [
    lambda c: c.update(items=[]),
    lambda c: c["items"][0].update(type="extra"),
    lambda c: c["items"][0].update(category="tools"),
    lambda c: c["items"][0].update(quantity=0),
    lambda c: c["items"][0].update(unit_price="abc"),
    lambda c: c.update(markup_pct=150),
    lambda c: c.update(schedule_days=1.5),
])
def test_bad_input_raises(sample, mutate):
    broken = copy.deepcopy(sample)
    mutate(broken)
    with pytest.raises(ValueError):
        change_order.compute(broken)


def test_markdown_contains_totals_and_signatures(sample):
    text = change_order.render_markdown(change_order.compute(sample))
    assert "# Change Order 2:" in text
    assert "**This change order: $544.50**" in text
    assert "**Revised contract sum: $19,494.50**" in text
    assert "-$60.00" in text
    assert "Adds 1 working day(s)." in text
    assert "SAMPLE VALUES ONLY" in text
    assert text.count("Date: __________") == 2


def test_cli(tmp_path, capsys):
    assert change_order.main([str(SAMPLE)]) == 0
    assert json.loads(capsys.readouterr().out)["change_total"] == "544.50"
    assert change_order.main([str(tmp_path / "missing.json")]) == 2
