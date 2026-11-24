import json
from pathlib import Path

import pytest

import takeoff

SAMPLE = Path(__file__).resolve().parent.parent / "skills/material-takeoff/examples/sample_room.json"


def test_wall_and_opening_area():
    assert takeoff.wall_area(8, 5, 8) == 208
    assert takeoff.openings_area([{"width_ft": 2, "height_ft": 3}, {"width_ft": 3, "height_ft": 7}]) == 27


def test_drywall_rounds_up_with_waste():
    assert takeoff.drywall_sheets(320)["quantity"] == 11  # 352 / 32
    assert takeoff.drywall_sheets(320, sheet="4x12")["quantity"] == 8  # 352 / 48 = 7.33
    assert takeoff.drywall_sheets(320, waste=0)["quantity"] == 10


def test_drywall_exact_fit_does_not_add_a_sheet():
    assert takeoff.drywall_sheets(64, waste=0)["quantity"] == 2
    assert takeoff.drywall_sheets(0)["quantity"] == 0


def test_tile_patterns_change_waste():
    straight = takeoff.tile_quantity(100, 12, 12)
    diagonal = takeoff.tile_quantity(100, 12, 12, pattern="diagonal")
    herringbone = takeoff.tile_quantity(100, 12, 12, pattern="herringbone")
    assert (straight["quantity"], diagonal["quantity"], herringbone["quantity"]) == (110, 115, 120)


def test_tile_boxes():
    line = takeoff.tile_quantity(40, 12, 24, tiles_per_box=8)
    assert line["tiles"] == 22 and line["quantity"] == 3 and line["unit"] == "box"


def test_paint_gallons():
    assert takeoff.paint_gallons(350, coats=1, waste=0)["quantity"] == 1
    assert takeoff.paint_gallons(350, coats=2)["quantity"] == 3  # 735 / 350 = 2.1
    assert takeoff.paint_gallons(400, coats=2, coverage_sqft_per_gal=400, waste=0)["quantity"] == 2


def test_trim_sticks():
    assert takeoff.trim_sticks(23.5)["quantity"] == 2  # 25.85 / 16
    assert takeoff.trim_sticks(32, stick_ft=8, waste=0)["quantity"] == 4


@pytest.mark.parametrize("call", [
    lambda: takeoff.drywall_sheets(-1),
    lambda: takeoff.drywall_sheets(100, sheet="5x9"),
    lambda: takeoff.drywall_sheets(100, waste=10),
    lambda: takeoff.tile_quantity(100, 0, 12),
    lambda: takeoff.tile_quantity(100, 12, 12, pattern="basket"),
    lambda: takeoff.tile_quantity(100, 12, 12, tiles_per_box=0),
    lambda: takeoff.paint_gallons(100, coats=0),
    lambda: takeoff.paint_gallons(100, coats=1.5),
    lambda: takeoff.trim_sticks(10, stick_ft=0),
    lambda: takeoff.wall_area("8", 5, 8),
    lambda: takeoff.drywall_sheets(float("inf")),
    lambda: takeoff.wall_area(float("nan"), 5, 8),
])
def test_bad_input_raises(call):
    with pytest.raises(ValueError):
        call()


def test_sample_room_end_to_end():
    result = takeoff.room_takeoff(json.loads(SAMPLE.read_text(encoding="utf-8")))
    geometry = result["geometry"]
    assert (geometry["floor_sqft"], geometry["gross_wall_sqft"], geometry["perimeter_ft"]) == (40.0, 208.0, 26.0)
    assert geometry["net_wall_sqft"] == pytest.approx(185.325, abs=0.01)
    by_unit = {line["unit"]: line["quantity"] for line in result["lines"]}
    assert by_unit == {"sheet": 8, "box": 3, "gallon": 2, "stick": 2}
    assert result["sample_material_total"] == 384.00
    assert "SAMPLE" in result["notice"]


def test_room_only_computes_requested_materials():
    result = takeoff.room_takeoff({"length_ft": 10, "width_ft": 10, "height_ft": 8, "paint": {"coats": 1}})
    assert [line["unit"] for line in result["lines"]] == ["gallon"]
    assert "sample_material_total" not in result


def test_openings_never_push_wall_area_negative():
    room = {"length_ft": 2, "width_ft": 2, "height_ft": 2,
            "windows": [{"width_ft": 10, "height_ft": 10}], "drywall": {}}
    result = takeoff.room_takeoff(room)
    assert result["geometry"]["net_wall_sqft"] == 0 and result["lines"][0]["quantity"] == 0


def test_cli_table_and_error(tmp_path, capsys):
    assert takeoff.main([str(SAMPLE), "--table"]) == 0
    out = capsys.readouterr().out
    assert "Drywall sheets 4x8" in out and "Sample material total: $384.00" in out
    bad = tmp_path / "bad.json"
    bad.write_text('{"length_ft": 8}', encoding="utf-8")
    assert takeoff.main([str(bad)]) == 2


def test_cli_rejects_infinity_without_a_traceback(tmp_path):
    bad = tmp_path / "inf.json"
    bad.write_text('{"length_ft": Infinity, "width_ft": 5, "height_ft": 8, "drywall": {}}', encoding="utf-8")
    assert takeoff.main([str(bad)]) == 2
