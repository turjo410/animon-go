"""Create a SYNTHETIC smoke-test dataset so the harness can be exercised end-to-end
before any real pilot photos exist.

!!! Results on this data say NOTHING about real-world accuracy. !!!
"Individuals" here are single internet photos (microsoft/cats_vs_dogs on Hugging Face)
re-augmented to fake extra "sessions" — far easier than a real animal photographed on
another day by another phone. Use it only to check that the scripts run.

Writes:
  data/_smoke/identity/<species>/<animal>/<session>__<phone>__<n>.jpg   (+ manifest.csv)
  data/_smoke/classify/{feline,canine,none}/*.jpg

Usage:  uv run make_smoke_data.py [--animals-per-species 15]
"""

from __future__ import annotations

import argparse
import io
import json
import random
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

HERE = Path(__file__).parent
API = "https://datasets-server.huggingface.co/rows?dataset=microsoft/cats_vs_dogs&config=default&split=train"


def fetch_rows(offset: int, length: int) -> list[dict]:
    with urllib.request.urlopen(f"{API}&offset={offset}&length={length}", timeout=60) as r:
        return json.load(r)["rows"]


def fetch_image(url: str) -> Image.Image:
    with urllib.request.urlopen(url, timeout=60) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def augment(img: Image.Image, rng: random.Random) -> Image.Image:
    w, h = img.size
    s = rng.uniform(0.75, 0.95)
    cw, ch = int(w * s), int(h * s)
    x, y = rng.randint(0, w - cw), rng.randint(0, h - ch)
    out = img.crop((x, y, x + cw, y + ch)).rotate(rng.uniform(-12, 12), expand=False)
    if rng.random() < 0.5:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    out = ImageEnhance.Brightness(out).enhance(rng.uniform(0.7, 1.3))
    out = ImageEnhance.Color(out).enhance(rng.uniform(0.7, 1.3))
    if rng.random() < 0.4:
        out = out.filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 1.5)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--animals-per-species", type=int, default=15)
    ap.add_argument("--classify-per-label", type=int, default=20)
    args = ap.parse_args()
    rng = random.Random(0)
    root = HERE / "data" / "_smoke"
    need = args.animals_per_species + args.classify_per_label

    # The dataset is sorted: cats first (label 0), dogs from roughly row 11.7k (label 1).
    pools: dict[str, list[str]] = {"cat": [], "dog": []}
    for sp, label, offset in (("cat", 0, 0), ("dog", 1, 11800)):
        while len(pools[sp]) < need:
            rows = fetch_rows(offset, 100)
            if not rows:
                raise SystemExit(f"Ran out of rows while collecting {sp} images")
            pools[sp] += [r["row"]["image"]["src"] for r in rows if r["row"]["labels"] == label]
            offset += 100
        pools[sp] = pools[sp][:need]

    phones = ["iphone13", "pixel7", "galaxyA14"]
    for sp, urls in pools.items():
        for i, url in enumerate(urls[: args.animals_per_species]):
            img = fetch_image(url)
            d = root / "identity" / sp / f"{sp}-{i:02d}"
            d.mkdir(parents=True, exist_ok=True)
            img.save(d / f"s1__{phones[0]}__000.jpg", quality=92)
            augment(img, rng).save(d / f"s1__{phones[0]}__001.jpg", quality=88)
            for s, ph in (("s2", phones[1]), ("s3", phones[2])):
                for n in range(2):
                    augment(img, rng).save(d / f"{s}__{ph}__{n:03d}.jpg", quality=rng.randint(70, 90))
        fam = "feline" if sp == "cat" else "canine"
        cd = root / "classify" / fam
        cd.mkdir(parents=True, exist_ok=True)
        for j, url in enumerate(urls[args.animals_per_species :]):
            fetch_image(url).save(cd / f"{j:03d}.jpg", quality=90)

    nd = root / "classify" / "none"
    nd.mkdir(parents=True, exist_ok=True)
    for j in range(args.classify_per_label):  # synthetic textures/gradients standing in for "no animal"
        a = np.linspace(0, 1, 224)[None, :, None] * rng.random() + np.random.default_rng(j).random((224, 224, 3)) * 0.4
        Image.fromarray((np.clip(a, 0, 1) * 255).astype("uint8")).save(nd / f"{j:03d}.jpg")

    print(f"Smoke data written to {root}")
    print("Next: uv run make_manifest.py data/_smoke/identity")


if __name__ == "__main__":
    main()
