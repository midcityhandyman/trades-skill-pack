"""Put each skill's scripts folder on sys.path so tests import the real files."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for folder in sorted((ROOT / "skills").glob("*/scripts")) + [ROOT / "tools"]:
    sys.path.insert(0, str(folder))
