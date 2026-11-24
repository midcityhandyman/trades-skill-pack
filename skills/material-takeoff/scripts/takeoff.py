#!/usr/bin/env python3
"""Deterministic material takeoff calculators for a single room.

Standard library only, so it runs in sandboxes with no package installs.
Every default below (waste factors, coverage rates) is a SAMPLE value for
illustration. Replace them with your own shop standards before real use.

Usage:
    python takeoff.py room.json            # JSON result
    python takeoff.py room.json --table    # plain text table
"""
from __future__ import annotations

import argparse
import json
import math
import sys

# SAMPLE waste factors, expressed as a fraction of the net quantity.
SAMPLE_WASTE = {
    "drywall": 0.10,
    "tile_straight": 0.10,
    "tile_diagonal": 0.15,
    "tile_herringbone": 0.20,
    "paint": 0.05,
    "trim": 0.10,
}
SHEET_SQFT = {"4x8": 32.0, "4x10": 40.0, "4x12": 48.0}
SAMPLE_PAINT_COVERAGE_SQFT_PER_GAL = 350.0


def _ceil(value: float) -> int:
    """Round up, ignoring float noise such as 3.0000000001."""
    return int(math.ceil(round(value, 6)))


def _check(name: str, value: float, allow_zero: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name} must be {'zero or more' if allow_zero else 'greater than zero'}")
    return float(value)


def _waste(key: str, override: float | None) -> float:
    waste = SAMPLE_WASTE[key] if override is None else override
    waste = _check("waste", waste)
    if waste >= 1:
        raise ValueError("waste is a fraction (0.10 means 10 percent), not a percent")
    return waste


def wall_area(length_ft: float, width_ft: float, height_ft: float) -> float:
    """Gross wall area of a rectangular room in square feet."""
    return 2 * (_check("length_ft", length_ft) + _check("width_ft", width_ft)) * _check("height_ft", height_ft)


def openings_area(openings: list[dict]) -> float:
    return sum(_check("width_ft", o["width_ft"]) * _check("height_ft", o["height_ft"]) for o in openings)


def drywall_sheets(area_sqft: float, sheet: str = "4x8", waste: float | None = None) -> dict:
    if sheet not in SHEET_SQFT:
        raise ValueError(f"sheet must be one of {sorted(SHEET_SQFT)}")
    area = _check("area_sqft", area_sqft)
    w = _waste("drywall", waste)
    return {
        "item": f"Drywall sheets {sheet}",
        "net": round(area, 2),
        "net_unit": "sqft",
        "waste_pct": round(w * 100, 1),
        "quantity": _ceil(area * (1 + w) / SHEET_SQFT[sheet]),
        "unit": "sheet",
    }


def tile_quantity(area_sqft: float, tile_w_in: float, tile_l_in: float, pattern: str = "straight",
                  tiles_per_box: int | None = None, waste: float | None = None) -> dict:
    key = f"tile_{pattern}"
    if key not in SAMPLE_WASTE:
        raise ValueError("pattern must be straight, diagonal or herringbone")
    area = _check("area_sqft", area_sqft)
    tile_sqft = _check("tile_w_in", tile_w_in, False) * _check("tile_l_in", tile_l_in, False) / 144.0
    w = _waste(key, waste)
    tiles = _ceil(area * (1 + w) / tile_sqft)
    line = {
        "item": f"Tile {tile_w_in:g}x{tile_l_in:g} in, {pattern} lay",
        "net": round(area, 2),
        "net_unit": "sqft",
        "waste_pct": round(w * 100, 1),
        "quantity": tiles,
        "unit": "tile",
    }
    if tiles_per_box is not None:
        if isinstance(tiles_per_box, bool) or not isinstance(tiles_per_box, int) or tiles_per_box < 1:
            raise ValueError("tiles_per_box must be a whole number of 1 or more")
        line["tiles"] = tiles
        line["quantity"] = _ceil(tiles / tiles_per_box)
        line["unit"] = "box"
    return line


def paint_gallons(area_sqft: float, coats: int = 2, waste: float | None = None,
                  coverage_sqft_per_gal: float = SAMPLE_PAINT_COVERAGE_SQFT_PER_GAL) -> dict:
    if isinstance(coats, bool) or not isinstance(coats, int) or coats < 1:
        raise ValueError("coats must be a whole number of 1 or more")
    area = _check("area_sqft", area_sqft)
    coverage = _check("coverage_sqft_per_gal", coverage_sqft_per_gal, False)
    w = _waste("paint", waste)
    return {
        "item": f"Paint, {coats} coat(s)",
        "net": round(area, 2),
        "net_unit": "sqft",
        "waste_pct": round(w * 100, 1),
        "quantity": _ceil(area * coats * (1 + w) / coverage),
        "unit": "gallon",
    }


def trim_sticks(linear_ft: float, stick_ft: float = 16, waste: float | None = None) -> dict:
    lf = _check("linear_ft", linear_ft)
    stick = _check("stick_ft", stick_ft, False)
    w = _waste("trim", waste)
    return {
        "item": f"Baseboard, {stick:g} ft sticks",
        "net": round(lf, 2),
        "net_unit": "lf",
        "waste_pct": round(w * 100, 1),
        "quantity": _ceil(lf * (1 + w) / stick),
        "unit": "stick",
    }


def room_takeoff(room: dict) -> dict:
    """Build a full takeoff from a room description (see examples/sample_room.json)."""
    length, width, height = room["length_ft"], room["width_ft"], room["height_ft"]
    doors, windows = room.get("doors", []), room.get("windows", [])
    floor = _check("length_ft", length, False) * _check("width_ft", width, False)
    gross = wall_area(length, width, height)
    net_walls = max(gross - openings_area(doors) - openings_area(windows), 0.0)
    perimeter = 2 * (length + width)
    lines = []

    if "drywall" in room:
        d = room["drywall"]
        area = net_walls + (floor if d.get("include_ceiling") else 0.0)
        lines.append(drywall_sheets(area, d.get("sheet", "4x8"), d.get("waste")))
    if "tile" in room:
        t = room["tile"]
        area = t.get("area_sqft", floor)
        lines.append(tile_quantity(area, t["tile_in"][0], t["tile_in"][1], t.get("pattern", "straight"),
                                   t.get("tiles_per_box"), t.get("waste")))
    if "paint" in room:
        p = room["paint"]
        area = net_walls + (floor if p.get("include_ceiling") else 0.0)
        lines.append(paint_gallons(area, p.get("coats", 2), p.get("waste")))
    if "trim" in room:
        r = room["trim"]
        base_lf = max(perimeter - sum(d["width_ft"] for d in doors), 0.0)
        lines.append(trim_sticks(base_lf, r.get("stick_ft", 16), r.get("waste")))

    result = {
        "label": room.get("label", "SAMPLE room"),
        "notice": "SAMPLE VALUES ONLY. Waste factors, coverage and prices are illustrative defaults.",
        "geometry": {
            "floor_sqft": round(floor, 2),
            "gross_wall_sqft": round(gross, 2),
            "net_wall_sqft": round(net_walls, 2),
            "perimeter_ft": round(perimeter, 2),
        },
        "lines": lines,
    }
    prices = room.get("sample_unit_prices")
    if prices:
        total = 0.0
        for line in lines:
            price = prices.get(line["unit"])
            if price is not None:
                line["sample_unit_price"] = round(_check("price", price), 2)
                line["sample_extended"] = round(line["quantity"] * price, 2)
                total += line["sample_extended"]
        result["sample_material_total"] = round(total, 2)
    return result


def format_table(result: dict) -> str:
    out = [f"Takeoff: {result['label']}", result["notice"], ""]
    out.append(f"{'Item':<36}{'Net':>10} {'Waste':>6} {'Order':>6} Unit")
    for line in result["lines"]:
        net = f"{line['net']:g} {line['net_unit']}"
        row = f"{line['item']:<36}{net:>10} {line['waste_pct']:>5g}% {line['quantity']:>6} {line['unit']}"
        if "sample_extended" in line:
            row += f"  (sample ${line['sample_extended']:.2f})"
        out.append(row)
    if "sample_material_total" in result:
        out.append(f"\nSample material total: ${result['sample_material_total']:.2f} (not a quote)")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Room material takeoff with SAMPLE waste factors.")
    parser.add_argument("room_json", help="path to a room description JSON file")
    parser.add_argument("--table", action="store_true", help="print a text table instead of JSON")
    args = parser.parse_args(argv)
    try:
        with open(args.room_json, encoding="utf-8") as handle:
            result = room_takeoff(json.load(handle))
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"takeoff error: {exc!r}", file=sys.stderr)
        return 2
    print(format_table(result) if args.table else json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
