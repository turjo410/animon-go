"""Write an identity manifest for the public Multi-pose Dog Dataset (MPDD).

Source: Mendeley Data, "Multi-pose dog dataset", doi:10.17632/v5j6m8dzhv.1, licence CC BY 4.0.
191 dogs, 1,656 pre-cropped photos, file names <dog>_c<camera>s<sequence>_<n>.jpg.
Download MPDD.zip into data/public_identity/mpdd_raw/ and extract to .../mpdd_raw/x/ first
(see README "Public pre-checks").

Mapping onto the harness:
  animal_id = dog id
  phone     = camera ("cam<k>")
  session   = camera + sequence ("c<k>s<j>"), so registration and probes are different captures

Caveats (this is EASIER than our real protocol): sequences may come from the same walk or day,
and some dogs wear distinctive clothing. It is a public pre-check, not evidence for the pilot.

Usage:  uv run import_mpdd.py   ->  data/public_identity/mpdd_manifest.csv
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE / "data" / "public_identity"
SRC = ROOT / "mpdd_raw" / "x" / "MPDD" / "pytorch"
PAT = re.compile(r"(\d+)_c(\d+)s(\d+)_(\d+)\.jpg$")


def main():
    if not SRC.exists():
        raise SystemExit(f"Not found: {SRC} — download and extract MPDD.zip first")
    rows = []
    for p in sorted(SRC.rglob("*.jpg")):
        m = PAT.match(p.name)
        if not m:
            continue
        dog, cam, seq, _ = m.groups()
        rows.append({
            "path": str(p.relative_to(ROOT)),
            "animal_id": f"dog/mpdd-{int(dog):03d}",
            "species": "dog",
            "session": f"c{cam}s{seq}",
            "phone": f"cam{cam}",
            "location": "",
        })
    out = ROOT / "mpdd_manifest.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}: {len(rows)} images, {len({r['animal_id'] for r in rows})} dogs")


if __name__ == "__main__":
    main()
