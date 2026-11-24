---
name: change-order-writer
description: Writes a residential remodeling change order with itemized adds and credits, markup, material tax, revised contract sum, schedule impact and signature lines. Use when the user mentions a change order, extra work, a client requested change, hidden damage found mid job, or needs to price and document a change to an existing scope or contract.
---

# Change Order Writer

A change order amends a signed scope. It must say what changed, why, what it costs, what
it does to the schedule, and it must be signed before the work starts. The price math is
done by a script. Never total a change order by hand.

## Workflow

1. Gather the facts: project label, original contract sum, total of prior approved
   change orders, the reason for the change, each added or removed item (quantity, unit,
   unit price, material or labor), markup percent, material tax percent, schedule days.
   Ask for any figure that is missing. Do not invent rates.
2. Classify the reason using [references/reasons.md](references/reasons.md).
3. Write the facts to JSON shaped like
   [examples/sample.json](examples/sample.json).
4. Run:

   ```bash
   python scripts/change_order.py change.json --markdown
   ```

5. Return the rendered document. Edit only the reason text and item descriptions for
   clarity. Do not change any number the script produced.

## Rules

- How markup, tax and credits are treated is in
  [references/pricing.md](references/pricing.md). If the user's contract says
  otherwise, tell them the script follows the documented rules and show the difference.
- Describe each item so a third party could verify it: location, material, quantity.
- A credit is entered as a positive quantity and price with `"type": "credit"`.
- The bundled example uses SAMPLE prices and rates. Say so if you show it.
- Exit code 2 means bad input. Fix the JSON and rerun.
