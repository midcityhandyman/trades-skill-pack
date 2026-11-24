---
name: material-takeoff
description: Calculates order quantities for drywall, tile, paint and baseboard trim from room dimensions, with waste factors applied and rounded up to whole purchasable units. Use when the user asks for a material takeoff, a materials list, how many sheets, boxes, gallons or sticks to buy, or wants quantities for a residential remodel room.
---

# Material Takeoff

Turn room measurements into an order list. The arithmetic is done by a script so the
numbers are the same every time. Never estimate quantities in your head.

## Workflow

1. Collect the room: length, width and ceiling height in feet, every door and window
   (width and height), and which materials are in play. Ask for anything missing.
   Do not guess a dimension.
2. Write the room to a JSON file shaped like [examples/sample_room.json](examples/sample_room.json).
3. Run the calculator:

   ```bash
   python scripts/takeoff.py room.json --table
   ```

   Drop `--table` for JSON when another step will consume the result.
4. Report the table. For each line state the net quantity, the waste percent used and
   the order quantity. Say which waste factors were defaults.
5. If the layout is not a plain rectangle, split it into rectangles, run each one, and
   add the order quantities only after showing each part.

## Rules

- Waste factors and coverage rates built into the script are SAMPLE defaults. See
  [references/waste-factors.md](references/waste-factors.md) for what they are and when
  to override them with `"waste"` in the JSON.
- Formulas and rounding are in [references/formulas.md](references/formulas.md). Read it
  before explaining a number to the user.
- Prices are optional. If `sample_unit_prices` is supplied the output is labelled as a
  sample total. Never present it as a quote.
- A script error (exit code 2) means the input is wrong. Fix the input and rerun. Do not
  fall back to manual math.
