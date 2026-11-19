"""Build a manifest CSV from a folder of photos.

Expected layout (one folder per real animal):

    data/identity/
      cat/
        cat-01-milo/
          s1__iphone13__001.jpg        <- session "s1", phone "iphone13"
          s2__pixel7__001.heic
        cat-02-luna/ ...
      dog/
        dog-01-rex/ ...

File names are  <session>__<phone>__<anything>.<ext>  (double underscores).
Use one session per capture occasion (different day and/or different person).
Files that do not follow the pattern get session "s1" and phone "unknown", with a warning.

Afterwards you may add columns by hand:
  location  - where the photo was taken (e.g. "home-A", "park-1"); enables the background-leakage check
  role      - "registered" or "unfamiliar" to fix the split yourself instead of the seeded default

Usage:
  uv run make_manifest.py data/identity            # writes data/identity/manifest.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from common import list_images


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = Path(sys.argv[1]).resolve()
    rows, warn = [], 0
    for species_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        for animal_dir in sorted(p for p in species_dir.iterdir() if p.is_dir()):
            for img in list_images(animal_dir):
                parts = img.stem.split("__")
                if len(parts) >= 3:
                    session, phone = parts[0], parts[1]
                else:
                    session, phone = "s1", "unknown"
                    warn += 1
                rows.append({
                    "path": str(img.relative_to(root)),
                    "animal_id": f"{species_dir.name}/{animal_dir.name}",
                    "species": species_dir.name.lower(),
                    "session": session,
                    "phone": phone,
                    "location": "",
                })
    if not rows:
        sys.exit(f"No images found under {root}/<species>/<animal>/")
    out = root / "manifest.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    animals = {r["animal_id"] for r in rows}
    print(f"Wrote {out}: {len(rows)} images, {len(animals)} animals")
    if warn:
        print(f"WARNING: {warn} files did not match <session>__<phone>__*.ext; they were put in session s1 / phone unknown")


if __name__ == "__main__":
    main()
