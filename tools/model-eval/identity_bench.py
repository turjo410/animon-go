"""Individual-identity benchmark: "is this the same cat/dog we have seen before?"

Implements the evaluation shape from docs/research/identity-pilot-setup-plan.md §7:
  * registered animals are enrolled from their FIRST session only;
  * their later sessions (other day / other phone / other person) are the probes;
  * held-out "unfamiliar" animals are never enrolled and must NOT be matched;
  * thresholds are calibrated on one half of the animals and frozen before
    being applied to the other half (no tuning on the test set);
  * every failure (e.g. no animal detected) is counted, never dropped.

Input: a manifest CSV (see make_manifest.py) with columns
  path, animal_id, species, session, phone[, location][, role]
role is optional: "registered" or "unfamiliar". If absent, unfamiliar animals are
picked deterministically per species with --unfamiliar-per-species.

Usage:
  uv run identity_bench.py --manifest data/identity/manifest.csv \
      --models dinov2-small dinov2-base siglip2-base clip-laion-b32 --crop both
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from common import BACKBONES, AnimalCropper, Embedder, Timer, batched, file_key, load_image, pick_device

HERE = Path(__file__).parent


@dataclass
class Item:
    path: Path
    animal_id: str
    species: str
    session: str
    phone: str
    location: str = ""
    role: str = ""
    split: str = ""  # "calib" | "test"
    is_gallery: bool = False
    emb: np.ndarray | None = None
    failed: str = ""  # failure reason, e.g. "no_animal_detected"


@dataclass
class ProbeResult:
    item: Item
    top1_id: str
    top1_sim: float
    top2_sim: float
    rank_of_true: int | None  # 1-based, None if animal not registered


# --------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------


def read_manifest(path: Path) -> list[Item]:
    items = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            p = Path(row["path"])
            if not p.is_absolute():
                p = (path.parent / p).resolve()
            items.append(
                Item(
                    path=p,
                    animal_id=row["animal_id"].strip(),
                    species=row.get("species", "").strip().lower(),
                    session=row.get("session", "s1").strip(),
                    phone=row.get("phone", "unknown").strip(),
                    location=row.get("location", "").strip(),
                    role=row.get("role", "").strip().lower(),
                )
            )
    missing = [i.path for i in items if not i.path.exists()]
    if missing:
        sys.exit(f"{len(missing)} manifest paths do not exist, e.g. {missing[0]}")
    return items


def assign_roles_and_splits(items: list[Item], unfamiliar_per_species: int, seed: int,
                            enroll_sessions: int = 1) -> list[str]:
    warnings: list[str] = []
    rng = random.Random(seed)
    by_animal: dict[str, list[Item]] = defaultdict(list)
    for it in items:
        by_animal[it.animal_id].append(it)

    # Roles
    if not any(it.role for it in items):
        by_species: dict[str, list[str]] = defaultdict(list)
        for aid, its in sorted(by_animal.items()):
            by_species[its[0].species].append(aid)
        for sp, aids in by_species.items():
            aids = sorted(aids)
            rng.shuffle(aids)
            unf = set(aids[:unfamiliar_per_species])
            for aid in aids:
                for it in by_animal[aid]:
                    it.role = "unfamiliar" if aid in unf else "registered"
    for aid, its in by_animal.items():
        roles = {it.role for it in its}
        if len(roles) != 1 or roles - {"registered", "unfamiliar"}:
            sys.exit(f"Animal {aid} has inconsistent/invalid role(s): {roles}")

    # Gallery = the earliest `enroll_sessions` sessions of each registered animal;
    # always leave at least one later session as probes.
    for aid, its in by_animal.items():
        if its[0].role != "registered":
            continue
        sessions = sorted({it.session for it in its})
        if len(sessions) < 2:
            warnings.append(f"{aid}: only one session ({sessions[0]}); enrolled but contributes no probes")
        n = max(1, min(enroll_sessions, len(sessions) - 1))
        for it in its:
            it.is_gallery = it.session in sessions[:n]

    # Calibration/test split by ANIMAL (stratified by role+species), so thresholds are
    # chosen on different animals than they are evaluated on.
    groups: dict[tuple, list[str]] = defaultdict(list)
    for aid, its in sorted(by_animal.items()):
        groups[(its[0].role, its[0].species)].append(aid)
    for key, aids in groups.items():
        aids = sorted(aids)
        rng.shuffle(aids)
        half = len(aids) // 2
        for k, aid in enumerate(aids):
            for it in by_animal[aid]:
                it.split = "calib" if k < half else "test"
        if len(aids) < 2:
            warnings.append(f"group {key} has <2 animals; calibration/test split is degenerate")
    return warnings


# --------------------------------------------------------------------------------------
# Embedding
# --------------------------------------------------------------------------------------


def embed_items(items, model_key, crop_mode, device, cache_dir: Path, batch_size: int, cropper_holder: dict):
    cache_dir.mkdir(parents=True, exist_ok=True)
    embedder = Embedder(BACKBONES[model_key], device)
    timer = Timer()
    todo: list[tuple[Item, object]] = []
    for it in items:
        it.emb, it.failed = None, ""
        key = file_key(it.path, model_key, crop_mode)
        cp = cache_dir / f"{key}.npy"
        fp = cache_dir / f"{key}.fail"
        if cp.exists():
            it.emb = np.load(cp)
            continue
        if fp.exists():
            it.failed = fp.read_text()
            continue
        img = load_image(it.path)
        if crop_mode == "rtdetr":
            if "c" not in cropper_holder:
                cropper_holder["c"] = AnimalCropper(device)
            c = cropper_holder["c"].crop(img, prefer=it.species or None)
            if c is None:
                it.failed = "no_animal_detected"
                fp.write_text(it.failed)
                continue
            img = c
        todo.append((it, img))
    for chunk in batched(todo, batch_size):
        embs = timer.time(embedder.embed, [img for _, img in chunk])
        timer.samples[-1] /= len(chunk)  # store per-image time
        for (it, _), e in zip(chunk, embs):
            it.emb = e
            np.save(cache_dir / f"{file_key(it.path, model_key, crop_mode)}.npy", e)
    # NaN when everything came from cache; delete results/cache to re-measure.
    return embedder.param_count, timer.summary_ms()


# --------------------------------------------------------------------------------------
# Matching + metrics
# --------------------------------------------------------------------------------------


def match(items: list[Item], agg: str) -> list[ProbeResult]:
    gallery = [it for it in items if it.is_gallery and it.emb is not None]
    if not gallery:
        sys.exit("Empty gallery: no registered animal has a usable enrollment image")
    ids = sorted({g.animal_id for g in gallery})
    idx = {a: k for k, a in enumerate(ids)}
    G = np.stack([g.emb for g in gallery])
    owner = np.array([idx[g.animal_id] for g in gallery])
    if agg == "mean":
        protos = np.stack([G[owner == k].mean(0) for k in range(len(ids))])
        protos /= np.linalg.norm(protos, axis=1, keepdims=True)
    results = []
    for it in items:
        if it.is_gallery or it.emb is None:
            continue
        if agg == "mean":
            per_id = protos @ it.emb
        else:
            sims = G @ it.emb
            per_id = np.full(len(ids), -1.0)
            np.maximum.at(per_id, owner, sims)
        order = np.argsort(-per_id)
        rank = None
        if it.role == "registered" and it.animal_id in idx:
            rank = int(np.where(order == idx[it.animal_id])[0][0]) + 1
        results.append(
            ProbeResult(
                item=it,
                top1_id=ids[order[0]],
                top1_sim=float(per_id[order[0]]),
                top2_sim=float(per_id[order[1]]) if len(order) > 1 else -1.0,
                rank_of_true=rank,
            )
        )
    return results


def is_false_candidate(r: ProbeResult) -> bool:
    """Would accepting this top-1 award the wrong animal (or an unregistered one)?"""
    return r.item.role == "unfamiliar" or r.top1_id != r.item.animal_id


def calibrate(calib: list[ProbeResult], max_missed_registered: float, accept_margin: float = 0.0, eps: float = 1e-4) -> dict:
    """accept = just above the highest similarity any wrong/unfamiliar probe reached on CALIB, plus a
    safety margin (small calibration sets underestimate the worst case)."""
    false_sims = [r.top1_sim for r in calib if is_false_candidate(r)]
    t_accept = (max(false_sims) + eps) if false_sims else min((r.top1_sim for r in calib), default=0.0)
    t_accept += accept_margin
    correct = sorted(r.top1_sim for r in calib if r.item.role == "registered" and not is_false_candidate(r))
    if correct:
        t_reject = float(np.quantile(correct, max_missed_registered))
    else:
        t_reject = t_accept
    t_reject = min(t_reject, t_accept)
    return {"accept": float(t_accept), "reject_below": float(t_reject), "n_false_in_calib": len(false_sims),
            "accept_margin": accept_margin}


def outcome(r: ProbeResult, th: dict) -> str:
    if r.top1_sim >= th["accept"]:
        if r.item.role == "unfamiliar":
            return "FALSE_ACCEPT_UNFAMILIAR"
        return "correct_match" if r.top1_id == r.item.animal_id else "WRONG_ANIMAL"
    if r.top1_sim >= th["reject_below"]:
        return "uncertain_review"
    return "missed_registered" if r.item.role == "registered" else "correct_unfamiliar"


def closed_set(results: list[ProbeResult]) -> dict:
    ranks = [r.rank_of_true for r in results if r.rank_of_true is not None]
    if not ranks:
        return {"rank1": float("nan"), "rank5": float("nan"), "mrr": float("nan"), "n": 0}
    a = np.array(ranks)
    return {"rank1": float((a == 1).mean()), "rank5": float((a <= 5).mean()), "mrr": float((1 / a).mean()), "n": len(a)}


def sweep(results: list[ProbeResult]) -> list[dict]:
    reg = [r for r in results if r.item.role == "registered"]
    unf = [r for r in results if r.item.role == "unfamiliar"]
    rows = []
    for t in np.round(np.arange(0.0, 1.0001, 0.01), 2):
        acc_reg = [r for r in reg if r.top1_sim >= t]
        rows.append(
            {
                "threshold": float(t),
                "true_accept_rate": sum(not is_false_candidate(r) for r in acc_reg) / max(1, len(reg)),
                "wrong_animal_rate": sum(is_false_candidate(r) for r in acc_reg) / max(1, len(reg)),
                "unfamiliar_accept_rate": sum(r.top1_sim >= t for r in unf) / max(1, len(unf)),
            }
        )
    return rows


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--models", nargs="+", default=list(BACKBONES), choices=list(BACKBONES))
    ap.add_argument("--crop", choices=["none", "rtdetr", "both"], default="both")
    ap.add_argument("--gallery-agg", choices=["max", "mean"], default="max")
    ap.add_argument("--enroll-sessions", type=int, default=1,
                    help="register each animal from its earliest N sessions (more enrollment photos)")
    ap.add_argument("--unfamiliar-per-species", type=int, default=5, help="§7 protocol: 5 of 15 per species")
    ap.add_argument("--max-missed-registered", type=float, default=0.05,
                    help="calibrate the lower threshold so at most this share of registered probes is called unfamiliar")
    ap.add_argument("--accept-margin", type=float, default=0.0,
                    help="added to the calibrated accept threshold; widens the uncertain band (safer, more operator review)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--out", type=Path, default=HERE / "results")
    ap.add_argument("--label", default="", help="free-text label stored in the report, e.g. 'SYNTHETIC SMOKE TEST'")
    args = ap.parse_args()

    items = read_manifest(args.manifest)
    warnings = assign_roles_and_splits(items, args.unfamiliar_per_species, args.seed, args.enroll_sessions)
    device = pick_device(args.device)
    run_dir = args.out / f"identity-{datetime.now():%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)
    crops = ["none", "rtdetr"] if args.crop == "both" else [args.crop]

    n_animals = Counter((it.role, it.species) for it in {it.animal_id: it for it in items}.values())
    summary = {
        "label": args.label,
        "manifest": str(args.manifest),
        "device": str(device),
        "n_images": len(items),
        "animals": {f"{r}/{s}": n for (r, s), n in sorted(n_animals.items())},
        "phones": sorted({it.phone for it in items}),
        "warnings": warnings,
        "runs": [],
    }
    probe_rows = []
    cropper_holder: dict = {}

    for model_key in args.models:
        for crop in crops:
            print(f"== {model_key} / crop={crop}", flush=True)
            params, lat = embed_items(items, model_key, crop, device, args.out / "cache", args.batch_size, cropper_holder)
            results = match(items, args.gallery_agg)
            calib = [r for r in results if r.item.split == "calib"]
            test = [r for r in results if r.item.split == "test"]
            th = calibrate(calib, args.max_missed_registered, args.accept_margin)
            outcomes = Counter(outcome(r, th) for r in test)
            failures = Counter(it.failed for it in items if it.failed)
            gallery_fail = sum(1 for it in items if it.is_gallery and it.failed)

            loc_conf = None
            if any(it.location for it in items):
                wrong = [r for r in results if r.item.role == "registered" and r.top1_id != r.item.animal_id]
                loc_of = {it.animal_id: it.location for it in items if it.is_gallery}
                if wrong:
                    loc_conf = sum(loc_of.get(r.top1_id) == r.item.location for r in wrong) / len(wrong)

            by_group = defaultdict(Counter)
            for r in test:
                by_group[f"species={r.item.species}"][outcome(r, th)] += 1
                by_group[f"phone={r.item.phone}"][outcome(r, th)] += 1

            run = {
                "model": model_key,
                "licence": BACKBONES[model_key].licence,
                "crop": crop,
                "params_m": round(params / 1e6, 1),
                "latency_per_image_ms_on_this_machine": {k: round(v, 1) for k, v in lat.items()},
                "closed_set_all": closed_set(results),
                "closed_set_test": closed_set(test),
                "thresholds_from_calib": th,
                "test_outcomes": dict(outcomes),
                "test_probe_count": len(test),
                "failures": dict(failures),
                "gallery_images_failed": gallery_fail,
                "wrong_top1_sharing_location": loc_conf,
                "test_outcomes_by_group": {k: dict(v) for k, v in sorted(by_group.items())},
            }
            summary["runs"].append(run)
            with open(run_dir / f"sweep_{model_key}_{crop}.csv", "w", newline="") as f:
                rows = sweep(results)
                w = csv.DictWriter(f, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
            for r in results:
                probe_rows.append(
                    {
                        "model": model_key, "crop": crop, "path": str(r.item.path), "animal_id": r.item.animal_id,
                        "species": r.item.species, "role": r.item.role, "split": r.item.split,
                        "session": r.item.session, "phone": r.item.phone, "top1_id": r.top1_id,
                        "top1_sim": round(r.top1_sim, 4), "margin": round(r.top1_sim - r.top2_sim, 4),
                        "rank_of_true": r.rank_of_true, "outcome": outcome(r, th) if r.item.split == "test" else "(calib)",
                    }
                )
            for it in items:
                if it.failed:
                    probe_rows.append({"model": model_key, "crop": crop, "path": str(it.path), "animal_id": it.animal_id,
                                       "species": it.species, "role": it.role, "split": it.split, "session": it.session,
                                       "phone": it.phone, "outcome": f"FAILED:{it.failed}"})

    with open(run_dir / "probes.csv", "w", newline="") as f:
        keys = ["model", "crop", "path", "animal_id", "species", "role", "split", "session", "phone",
                "top1_id", "top1_sim", "margin", "rank_of_true", "outcome"]
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(probe_rows)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "summary.md").write_text(render_md(summary))
    print(render_md(summary))
    print(f"\nWrote {run_dir}")


def render_md(s: dict) -> str:
    L = [f"# Identity benchmark — {s['label'] or 'unlabelled run'}", ""]
    L += [f"- Manifest: `{s['manifest']}`  ", f"- Device: {s['device']} (latency is NOT phone/server latency)  ",
          f"- Images: {s['n_images']}; animals: {s['animals']}; phones: {', '.join(s['phones'])}", ""]
    if s["warnings"]:
        L += ["**Warnings**", ""] + [f"- {w}" for w in s["warnings"]] + [""]
    L += ["## Results on held-out TEST animals (thresholds frozen from CALIB animals)", "",
          "| model | crop | rank-1 | correct match | WRONG animal | FALSE accept (unfamiliar) | uncertain → review | missed registered | correct unfamiliar | failures | accept ≥ | review ≥ | ms/img |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in s["runs"]:
        o, n = r["test_outcomes"], max(1, r["test_probe_count"])
        pct = lambda k: f"{o.get(k, 0)} ({o.get(k, 0) / n:.0%})"
        L.append(
            f"| {r['model']} | {r['crop']} | {r['closed_set_test']['rank1']:.0%} | {pct('correct_match')} | "
            f"{pct('WRONG_ANIMAL')} | {pct('FALSE_ACCEPT_UNFAMILIAR')} | {pct('uncertain_review')} | "
            f"{pct('missed_registered')} | {pct('correct_unfamiliar')} | {sum(r['failures'].values())} | "
            f"{r['thresholds_from_calib']['accept']:.3f} | {r['thresholds_from_calib']['reject_below']:.3f} | "
            f"{r['latency_per_image_ms_on_this_machine']['median_ms']:.0f} |"
        )
    L += ["", "**How to read this.** A candidate is only viable if WRONG animal and FALSE accept are 0 on the test animals. "
          "Among viable candidates prefer the highest *correct match* and lowest *uncertain*. "
          "With ~30 animals, 0 errors is preliminary evidence, not proof (setup plan §7).", ""]
    for r in s["runs"]:
        if r.get("wrong_top1_sharing_location") is not None:
            L.append(f"- {r['model']}/{r['crop']}: {r['wrong_top1_sharing_location']:.0%} of wrong top-1 matches share the probe's location (background leakage signal)")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
