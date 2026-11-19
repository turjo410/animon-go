"""Family-classification benchmark (SRS FR-101..103, NFR-ACC-1).

Question: given a photo, is it Feline / Canine / Avian / Rodent / Insect — or no confident animal?

Data layout (one folder per true label; "none" = no animal, toys, screens, statues ...):

    data/classify/
      feline/  canine/  avian/  rodent/  insect/  none/

Optionally use sub-folders or a "<session>__<phone>__*.jpg" naming; only the top folder matters.

Method (mirrors FR-103's per-family thresholds):
  * images are split 50/50 (seeded, stratified by label) into CALIB and TEST;
  * for each family a confidence threshold is chosen on CALIB as the lowest value at which
    the false-award rate for that family is <= --max-false-award-rate (default 0 = none);
  * those frozen thresholds are applied to TEST. Below threshold => "no confident match"
    (a soft fail, which is the safe outcome).

This runs offline on a laptop. It ranks candidates; it does NOT replace the on-device
latency test in apps/mobile (see docs/research/model-evaluation-plan.md, step 5).

Usage:
  uv run classify_bench.py --data data/classify
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from common import Timer, list_images, load_image, pick_device

HERE = Path(__file__).parent
FAMILIES = ["feline", "canine", "avian", "rodent", "insect"]
LABELS = FAMILIES + ["none"]

PROMPTS = {
    "feline": ["a photo of a cat", "a photo of a kitten", "a photo of a wild cat"],
    "canine": ["a photo of a dog", "a photo of a puppy", "a photo of a fox"],
    "avian": ["a photo of a bird", "a photo of a pigeon", "a photo of a crow", "a photo of a sparrow"],
    "rodent": ["a photo of a rodent", "a photo of a squirrel", "a photo of a rat", "a photo of a mouse animal"],
    "insect": ["a photo of an insect", "a photo of a butterfly", "a photo of a bee", "a photo of a beetle"],
    "none": ["a photo of a street", "a photo of a room", "a photo of plants", "a photo of a toy",
             "a photo of a screen", "a photo of a person"],
}

CANDIDATES = {
    # key: (kind, hf/timm id, licence)
    "zeroshot-siglip2-base": ("siglip", "google/siglip2-base-patch16-224", "Apache-2.0"),
    "zeroshot-clip-laion-b32": ("clip", "laion/CLIP-ViT-B-32-laion2B-s34B-b79K", "MIT"),
    "imagenet-mobilenetv3-large": ("timm", "mobilenetv3_large_100.ra_in1k", "EVAL-ONLY baseline: ImageNet-trained, commercial clearance unresolved (licence screen)"),
    "imagenet-efficientnet-b0": ("timm", "efficientnet_b0.ra_in1k", "EVAL-ONLY baseline: ImageNet-trained, commercial clearance unresolved (licence screen)"),
}


class ZeroShot:
    """Text-prompted classifier. Scores = softmax over all prompts, summed per label."""

    def __init__(self, hf_id: str, device):
        from transformers import AutoModel, AutoProcessor

        self.device = device
        self.proc = AutoProcessor.from_pretrained(hf_id)
        self.model = AutoModel.from_pretrained(hf_id).to(device).eval()
        # Only the image tower ships on-device; text prompts are embedded once, ahead of time.
        vision = getattr(self.model, "vision_model", self.model)
        self.params = sum(p.numel() for p in vision.parameters()) + sum(
            p.numel() for p in getattr(self.model, "visual_projection", torch.nn.Identity()).parameters())
        texts, self.owner = [], []
        for lab in LABELS:
            for t in PROMPTS[lab]:
                texts.append(t)
                self.owner.append(LABELS.index(lab))
        self.owner = torch.tensor(self.owner)
        with torch.no_grad():
            ti = self.proc(text=texts, padding="max_length", max_length=64, return_tensors="pt", truncation=True).to(device)
            tf = self.model.get_text_features(**ti)
            tf = tf if isinstance(tf, torch.Tensor) else tf.pooler_output
            self.text = torch.nn.functional.normalize(tf.float(), dim=-1)

    @torch.no_grad()
    def __call__(self, img) -> np.ndarray:
        ii = self.proc(images=[img], return_tensors="pt").to(self.device)
        f = self.model.get_image_features(**ii)
        f = f if isinstance(f, torch.Tensor) else f.pooler_output
        f = torch.nn.functional.normalize(f.float(), dim=-1)
        scale = self.model.logit_scale.exp() if hasattr(self.model, "logit_scale") else 100.0
        logits = scale * f @ self.text.T
        p = logits.softmax(-1)[0].cpu()
        out = torch.zeros(len(LABELS))
        out.index_add_(0, self.owner, p)
        return out.numpy()


class ImageNetFamily:
    """ImageNet-1k classifier; family score = summed probability of that family's classes."""

    def __init__(self, timm_id: str, device):
        import timm

        self.device = device
        self.model = timm.create_model(timm_id, pretrained=True).to(device).eval()
        self.params = sum(p.numel() for p in self.model.parameters())
        cfg = timm.data.resolve_data_config({}, model=self.model)
        self.tf = timm.data.create_transform(**cfg)
        fam_map = json.loads((HERE / "imagenet_family_map.json").read_text())["indices"]
        self.groups = [torch.tensor(fam_map[f]) for f in FAMILIES]

    @torch.no_grad()
    def __call__(self, img) -> np.ndarray:
        x = self.tf(img).unsqueeze(0).to(self.device)
        p = self.model(x).softmax(-1)[0].cpu()
        fam = torch.stack([p[g].sum() for g in self.groups])
        return torch.cat([fam, (1 - fam.sum()).clamp(min=0).unsqueeze(0)]).numpy()


def build(key, device):
    kind, mid, _ = CANDIDATES[key]
    return ImageNetFamily(mid, device) if kind == "timm" else ZeroShot(mid, device)


def choose_thresholds(calib, max_rate):
    """Per family: lowest threshold whose false-award rate on CALIB is <= max_rate."""
    th = {}
    for k, fam in enumerate(FAMILIES):
        awarded = [(s[k], y) for s, y in calib if int(np.argmax(s[:5])) == k]
        best = 1.01
        for t in sorted({round(float(c), 4) for c, _ in awarded} | {1.0}, reverse=True):
            got = [y for c, y in awarded if c >= t]
            if not got:
                continue
            if sum(y != fam for y in got) / len(got) <= max_rate:
                best = t
            else:
                break
        th[fam] = best
    return th


def decide(scores, th):
    k = int(np.argmax(scores[:5]))
    return FAMILIES[k] if scores[k] >= th[FAMILIES[k]] else "no_confident_match"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--models", nargs="+", default=list(CANDIDATES), choices=list(CANDIDATES))
    ap.add_argument("--max-false-award-rate", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    data = []
    for lab in LABELS:
        imgs = list_images(args.data / lab) if (args.data / lab).exists() else []
        rng.shuffle(imgs)
        half = len(imgs) // 2
        data += [(p, lab, "calib" if i < half else "test") for i, p in enumerate(imgs)]
    counts = Counter(lab for _, lab, _ in data)
    missing = [l for l in LABELS if counts[l] == 0]
    device = pick_device(args.device)
    run_dir = args.out / f"classify-{datetime.now():%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)

    report = {"label": args.label, "data": str(args.data), "device": str(device), "counts": dict(counts),
              "missing_labels": missing, "runs": []}
    rows = []
    images = {p: load_image(p) for p, _, _ in data}
    for key in args.models:
        print(f"== {key}", flush=True)
        clf = build(key, device)
        timer = Timer()
        scored = [(timer.time(clf, images[p]), lab, split, p) for p, lab, split in data]
        calib = [(s, lab) for s, lab, sp, _ in scored if sp == "calib"]
        th = choose_thresholds(calib, args.max_false_award_rate)
        conf = defaultdict(Counter)
        for s, lab, sp, p in scored:
            d = decide(s, th)
            if sp == "test":
                conf[lab][d] += 1
            rows.append({"model": key, "path": str(p), "label": lab, "split": sp, "decision": d,
                         **{f"score_{l}": round(float(v), 4) for l, v in zip(LABELS, s)}})
        test_n = sum(sum(c.values()) for c in conf.values())
        false_awards = sum(n for lab, c in conf.items() for d, n in c.items() if d in FAMILIES and d != lab)
        per_family = {}
        for fam in FAMILIES:
            n = sum(conf[fam].values())
            per_family[fam] = {"n_test": n, "confident_correct": conf[fam][fam],
                               "coverage": conf[fam][fam] / n if n else None, "threshold": th[fam]}
        none_n = sum(conf["none"].values())
        report["runs"].append({
            "model": key, "licence": CANDIDATES[key][2], "params_m": round(clf.params / 1e6, 1),
            "latency_ms_on_this_machine": {k: round(v, 1) for k, v in timer.summary_ms().items()},
            "test_images": test_n, "false_awards": false_awards,
            "none_correctly_rejected": (conf["none"]["no_confident_match"] / none_n) if none_n else None,
            "per_family": per_family, "confusion_test": {k: dict(v) for k, v in conf.items()},
        })
    with open(run_dir / "predictions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (run_dir / "summary.json").write_text(json.dumps(report, indent=2))
    md = render_md(report)
    (run_dir / "summary.md").write_text(md)
    print(md)
    print(f"\nWrote {run_dir}")


def render_md(r):
    L = [f"# Family classification benchmark — {r['label'] or 'unlabelled run'}", "",
         f"- Data: `{r['data']}`; device {r['device']} (latency is NOT phone latency)", f"- Images per label: {r['counts']}"]
    if r["missing_labels"]:
        L.append(f"- **Missing labels (results incomplete): {', '.join(r['missing_labels'])}**")
    L += ["", "## TEST split, per-family thresholds frozen from CALIB", "",
          "| model | image-side params (M) | false awards | none rejected | " + " | ".join(f"{f} coverage" for f in FAMILIES) + " | ms/img |",
          "|---|---|---|---|" + "---|" * len(FAMILIES) + "---|"]
    for run in r["runs"]:
        cov = [run["per_family"][f]["coverage"] for f in FAMILIES]
        cov_s = " | ".join("n/a" if c is None else f"{c:.0%}" for c in cov)
        nr = run["none_correctly_rejected"]
        L.append(f"| {run['model']} | {run['params_m']} | {run['false_awards']} / {run['test_images']} | "
                 f"{'n/a' if nr is None else f'{nr:.0%}'} | {cov_s} | {run['latency_ms_on_this_machine']['median_ms']:.0f} |")
    L += ["", "**How to read this.** *False awards* (a creature granted for the wrong family or for a no-animal photo) must be ~0. "
          "*Coverage* = share of real animals of that family that get a confident award; higher is better. "
          "Shortlist the best 1–2 for the on-device test.", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
