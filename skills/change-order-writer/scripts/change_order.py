#!/usr/bin/env python3
"""Deterministic change order math and a markdown renderer.

Standard library only. Money is handled with Decimal and rounded half up to
cents. All rates in the bundled example are SAMPLE values.

Rules (documented in references/pricing.md):
  * Each item is an "add" or a "credit", in category "material" or "labor".
  * Markup applies to the net subtotal only when that net is positive.
    Net credits are returned without markup.
  * Material tax applies to net material only when that net is positive.
  * Revised contract sum = original + prior approved changes + this change.

Usage:
    python change_order.py change.json              # JSON totals
    python change_order.py change.json --markdown   # printable document
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _dec(name: str, value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{name} must be a number, got {value!r}") from None
    if not number.is_finite():
        raise ValueError(f"{name} must be finite")
    return number


def _pct(name: str, value) -> Decimal:
    pct = _dec(name, value)
    if pct < 0 or pct > 100:
        raise ValueError(f"{name} must be between 0 and 100")
    return pct / Decimal("100")


def compute(change: dict) -> dict:
    items = change.get("items") or []
    if not items:
        raise ValueError("a change order needs at least one item")
    lines, nets = [], {"material": ZERO, "labor": ZERO}
    for index, item in enumerate(items, start=1):
        kind, category = item.get("type"), item.get("category")
        if kind not in ("add", "credit"):
            raise ValueError(f"item {index}: type must be add or credit")
        if category not in nets:
            raise ValueError(f"item {index}: category must be material or labor")
        qty = _dec(f"item {index} quantity", item["quantity"])
        price = _dec(f"item {index} unit_price", item["unit_price"])
        if qty <= 0 or price < 0:
            raise ValueError(f"item {index}: quantity must be positive and unit_price zero or more")
        extended = money(qty * price) * (1 if kind == "add" else -1)
        nets[category] += extended
        lines.append({
            "description": item["description"], "type": kind, "category": category,
            "quantity": str(qty), "unit": item.get("unit", "ea"),
            "unit_price": str(money(price)), "extended": str(extended),
        })

    subtotal = nets["material"] + nets["labor"]
    markup = money(subtotal * _pct("markup_pct", change.get("markup_pct", 0))) if subtotal > 0 else ZERO
    tax_rate = _pct("material_tax_pct", change.get("material_tax_pct", 0))
    tax = money(nets["material"] * tax_rate) if nets["material"] > 0 else ZERO
    total = money(subtotal + markup + tax)
    original = money(_dec("original_contract_sum", change["original_contract_sum"]))
    prior = money(_dec("prior_approved_changes", change.get("prior_approved_changes", 0)))
    days = change.get("schedule_days", 0)
    if isinstance(days, bool) or not isinstance(days, int):
        raise ValueError("schedule_days must be a whole number (negative means time saved)")
    return {
        "change_order_number": change.get("change_order_number", 1),
        "project_label": change.get("project_label", "SAMPLE project"),
        "reason": change.get("reason", ""),
        "lines": lines,
        "material_net": str(money(nets["material"])),
        "labor_net": str(money(nets["labor"])),
        "subtotal": str(money(subtotal)),
        "markup": str(markup),
        "material_tax": str(tax),
        "change_total": str(total),
        "original_contract_sum": str(original),
        "prior_approved_changes": str(prior),
        "revised_contract_sum": str(money(original + prior + total)),
        "schedule_days": days,
    }


def _usd(text: str) -> str:
    value = Decimal(text)
    return f"{'-' if value < 0 else ''}${abs(value):,.2f}"


def render_markdown(result: dict) -> str:
    days = result["schedule_days"]
    schedule = "No change to the schedule." if days == 0 else (
        f"Adds {days} working day(s)." if days > 0 else f"Removes {-days} working day(s).")
    out = [
        f"# Change Order {result['change_order_number']}: {result['project_label']}",
        "",
        "> SAMPLE VALUES ONLY. Every price and quantity here is illustrative.",
        "",
        "## Reason for change",
        result["reason"] or "(not provided)",
        "",
        "## Items",
        "| # | Description | Type | Category | Qty | Unit | Unit price | Extended |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for number, line in enumerate(result["lines"], start=1):
        out.append(f"| {number} | {line['description']} | {line['type']} | {line['category']} | "
                   f"{line['quantity']} | {line['unit']} | {_usd(line['unit_price'])} | {_usd(line['extended'])} |")
    out += [
        "",
        "## Price",
        f"- Net material: {_usd(result['material_net'])}",
        f"- Net labor: {_usd(result['labor_net'])}",
        f"- Markup: {_usd(result['markup'])}",
        f"- Material tax: {_usd(result['material_tax'])}",
        f"- **This change order: {_usd(result['change_total'])}**",
        "",
        "## Contract sum",
        f"- Original contract sum: {_usd(result['original_contract_sum'])}",
        f"- Prior approved changes: {_usd(result['prior_approved_changes'])}",
        f"- **Revised contract sum: {_usd(result['revised_contract_sum'])}**",
        "",
        "## Schedule",
        schedule,
        "",
        "## Approval",
        "Work in this change order starts only after both parties sign.",
        "",
        "Owner: ____________________  Date: __________",
        "",
        "Contractor: ____________________  Date: __________",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute and render a change order.")
    parser.add_argument("change_json", help="path to a change order JSON file")
    parser.add_argument("--markdown", action="store_true", help="print the document instead of JSON")
    args = parser.parse_args(argv)
    try:
        with open(args.change_json, encoding="utf-8") as handle:
            result = compute(json.load(handle))
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print(f"change order error: {exc!r}", file=sys.stderr)
        return 2
    print(render_markdown(result) if args.markdown else json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
