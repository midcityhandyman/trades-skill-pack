#!/usr/bin/env python3
"""Offline demo: runs each skill's helper script the way a skill would call it.

No network, no keys. All inputs are invented sample values.
Usage: python demo/run_demo.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
STEPS = [
    ("1. Validate skill format", ["tools/validate_skills.py"]),
    ("2. material-takeoff: sample hall bath",
     ["skills/material-takeoff/scripts/takeoff.py", "skills/material-takeoff/examples/sample_room.json", "--table"]),
    ("3. change-order-writer: sample concealed condition",
     ["skills/change-order-writer/scripts/change_order.py",
      "skills/change-order-writer/examples/sample.json", "--markdown"]),
    ("4. scope-of-work-writer: lint a clean sample scope",
     ["skills/scope-of-work-writer/scripts/scope_lint.py", "skills/scope-of-work-writer/examples/sample_scope.md"]),
    ("5. scope-of-work-writer: lint a deliberately flawed draft (exit code 1 expected)",
     ["skills/scope-of-work-writer/scripts/scope_lint.py", "skills/scope-of-work-writer/examples/flawed_scope.md"]),
]
EXPECTED_EXIT = [0, 0, 0, 0, 1]


def main() -> int:
    print("trades-skill-pack demo. ALL PRICES AND QUANTITIES ARE SAMPLE VALUES.")
    ok = True
    for (title, command), expected in zip(STEPS, EXPECTED_EXIT):
        print(f"\n=== {title} ===")
        print(f"$ python {' '.join(command)}")
        done = subprocess.run([sys.executable, *command], cwd=ROOT, capture_output=True, text=True)
        print(done.stdout.rstrip())
        if done.stderr.strip():
            print(done.stderr.rstrip())
        print(f"[exit code {done.returncode}]")
        ok = ok and done.returncode == expected
    print("\nDemo finished: " + ("all steps behaved as expected." if ok else "UNEXPECTED EXIT CODE, see above."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
