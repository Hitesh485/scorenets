"""Bump boot.js?v=20260909cv -> 20260909fav in HTML shells."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "boot.js?v=20260909cv"
NEW = "boot.js?v=20260909fav"
changed = []
for path in ROOT.rglob("*.html"):
    if "node_modules" in path.parts:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if OLD not in text:
        continue
    path.write_text(text.replace(OLD, NEW), encoding="utf-8")
    changed.append(str(path.relative_to(ROOT)))
print("changed", len(changed))
for c in changed:
    print(c)
