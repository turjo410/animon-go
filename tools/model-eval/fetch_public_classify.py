"""Build a PUBLIC pre-check set for family classification from iNaturalist.

Why: real phone photos of the animals players will actually meet (pigeons, crows,
mynas, rats, mice, squirrels, insects, cats, dogs), available before our own photo
collection exists. It is a pre-check, not a substitute: our own photos (plan step 3)
remain the real test.

Licensing: only photos licensed CC0 or CC-BY are downloaded. Every image's licence and
attribution is written to data/public_classify/ATTRIBUTION.csv. Images stay local
(data/ is git-ignored) and are used only for internal evaluation.

"none" (no animal) here = iNaturalist plant and fungus photos, which are real outdoor
phone photos. Rooms, streets, toys and screens are NOT covered; they come from our own set.

Usage:  uv run fetch_public_classify.py [--scale 1.0] [--seed 7]
Then:   uv run classify_bench.py --data data/public_classify --label "iNaturalist pre-check"
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
API = "https://api.inaturalist.org/v1/observations"
UA = "animon-model-eval/0.1 (internal research; contact via repo owner)"

# label -> list of (iNaturalist taxon_id, name, count). Species chosen for what players
# meet in cities, including South Asia (house crow, common myna, palm squirrel).
PLAN: dict[str, list[tuple[int, str, int]]] = {
    "feline": [(118552, "Felis catus (domestic cat)", 60)],
    "canine": [(47144, "Canis familiaris (dog)", 45), (42054, "Vulpes (foxes)", 15)],
    "avian": [
        (3017, "Columba livia (pigeon)", 15),
        (8031, "Corvus splendens (house crow)", 15),
        (204454, "Acridotheres tristis (common myna)", 15),
        (13858, "Passer domesticus (house sparrow)", 15),
    ],
    "rodent": [
        (44540, "Rattus (rats)", 20),
        (44705, "Mus musculus (house mouse)", 15),
        (45936, "Funambulus pennantii (palm squirrel)", 12),
        (46017, "Sciurus carolinensis (grey squirrel)", 13),
    ],
    "insect": [
        (47219, "Apis mellifera (honey bee)", 10),
        (120156, "Musca domestica (house fly)", 10),
        (48662, "Danaus plexippus (monarch butterfly)", 10),
        (48486, "Coccinellidae (ladybirds)", 10),
        (47792, "Odonata (dragonflies)", 10),
        (52134, "Culicidae (mosquitoes)", 5),
        (47336, "Formicidae (ants)", 5),
    ],
    "none": [(47126, "Plantae (plants)", 70), (47170, "Fungi", 30)],
}


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def collect(taxon_id: int, n: int, rng: random.Random, per_user_cap: int = 2) -> list[dict]:
    params = {"taxon_id": taxon_id, "photo_license": "cc0,cc-by", "per_page": 200, "order_by": "created_at"}
    first = get_json(f"{API}?{urllib.parse.urlencode({**params, 'per_page': 1})}")
    total = first["total_results"]
    pages = list(range(1, max(1, min(50, total // 200)) + 1))
    rng.shuffle(pages)
    picked, users, seen = [], Counter(), set()
    for page in pages:
        time.sleep(1.0)  # be polite to the iNaturalist API (~1 request/second)
        for o in get_json(f"{API}?{urllib.parse.urlencode({**params, 'page': page})}")["results"]:
            photos = [p for p in o.get("photos", []) if p.get("license_code") in ("cc0", "cc-by")]
            user = (o.get("user") or {}).get("login", "?")
            if not photos or o["id"] in seen or users[user] >= per_user_cap:
                continue
            url = photos[0]["url"].replace("/square.", "/medium.")
            if not url.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            seen.add(o["id"])
            users[user] += 1
            picked.append({"obs_id": o["id"], "url": url, "license": photos[0]["license_code"],
                           "attribution": photos[0].get("attribution", ""), "user": user})
        if len(picked) >= n * 2:
            break
    rng.shuffle(picked)
    return picked[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0, help="multiply every count (e.g. 0.5 for a quick run)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=HERE / "data" / "public_classify")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, taxa in PLAN.items():
        d = args.out / label
        d.mkdir(exist_ok=True)
        for taxon_id, name, count in taxa:
            n = max(1, round(count * args.scale))
            items = collect(taxon_id, n, rng)
            ok = 0
            for it in items:
                dest = d / f"inat_{it['obs_id']}.jpg"
                if not dest.exists():
                    try:
                        dest.write_bytes(fetch_bytes(it["url"]))
                    except Exception as e:  # noqa: BLE001 - skip broken images, keep going
                        print(f"  skip {it['obs_id']}: {e}")
                        continue
                ok += 1
                rows.append({"label": label, "taxon": name, "file": str(dest.relative_to(args.out)), **it})
            print(f"{label:7s} {name:42s} {ok}/{n}")
    with open(args.out / "ATTRIBUTION.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} images in {args.out}; licences: {dict(Counter(r['license'] for r in rows))}")


if __name__ == "__main__":
    main()
