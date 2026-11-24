---
name: scope-of-work-writer
description: Drafts a clear residential remodeling scope of work with inclusions, exclusions, allowances, assumptions, schedule, payment schedule and change process, then lints the draft for missing sections and vague wording. Use when the user asks for a scope of work, SOW, job scope, project writeup or proposal scope for a bathroom, kitchen, basement or other home remodel, or wants an existing scope reviewed.
---

# Scope of Work Writer

A scope of work is the document both sides point to when they disagree. Write it so a
stranger could tell what is and is not being done.

## Workflow

1. Gather the job facts: rooms, what is being removed, what is being installed, who
   supplies which materials, known site conditions, target dates, payment terms. Ask for
   what is missing. Mark anything unknown as an assumption, never as a fact.
2. Draft the scope in markdown using the section order in
   [references/template.md](references/template.md).
3. Save the draft and lint it:

   ```bash
   python scripts/scope_lint.py scope.md
   ```

4. Fix every error and reword every warning, then rerun until it prints
   `scope lint: clean, 0 findings`.
5. Return the scope. List the assumptions you made at the end of your reply so the user
   can confirm them.

## Rules

- Every inclusion names a location, a material or product level, and a quantity or
  extent. See [references/wording.md](references/wording.md) for rewrites of
  common vague lines.
- Exclusions are as important as inclusions. Always state the usual ones for the trade
  (permits, hidden damage, hazardous materials, owner supplied items).
- Every allowance has a dollar amount and says what happens to the difference.
- Payment percentages must add up to 100.
- Quantities come from the material-takeoff skill when it is installed. Do not invent
  them.
- Any price in the bundled example is a SAMPLE value.

To review a scope someone else wrote, skip to step 3 and report the findings.
