"""Animal identity demo: register individual animals from several angles, then identify new photos.

Research demo only, not the live product. Runs locally; photos never leave this machine.

  * Finding the animal: RT-DETRv2 detector (Apache-2.0) crops it, so the background doesn't
    dominate the match.
  * Animal type (dog / cat / bird / ...): OpenCLIP ViT-B/32 LAION (MIT), zero-shot: the crop is
    compared with text descriptions such as "a photo of a dog".
  * Individual identity: DINOv2-base (Apache-2.0) turns each crop into 768 numbers; two photos of
    the same animal give similar numbers. "Similarity %" = cosine similarity x 100.
  * Verdict thresholds default to the values calibrated on 191 public dogs
    (docs/research/results/2026-11-10-identity-public-precheck.md) and can be changed in the sidebar.

Run:  cd tools/model-eval && uv run --extra app streamlit run app/animal_id_app.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import BACKBONES, AnimalCropper, Embedder, load_image, pick_device  # noqa: E402

GALLERY = ROOT / "data" / "app_gallery"  # git-ignored (data/)
DEMO_MANIFEST = ROOT / "data" / "public_identity" / "mpdd_manifest.csv"
MODEL_KEY = "dinov2-base"
DEFAULT_ACCEPT, DEFAULT_REVIEW = 0.75, 0.52
TYPE_MODEL_KEY = "clip-laion-b32"
# display name -> (emoji, text prompts). Several prompts per type are averaged.
ANIMAL_TYPES = {
    "dog": ("🐶", ["a photo of a dog", "a photo of a puppy"]),
    "cat": ("🐱", ["a photo of a cat", "a photo of a kitten"]),
    "bird": ("🐦", ["a photo of a bird", "a photo of a pigeon", "a photo of a crow", "a photo of a sparrow"]),
    "rodent": ("🐀", ["a photo of a rat", "a photo of a mouse", "a photo of a hamster"]),
    "squirrel": ("🐿️", ["a photo of a squirrel"]),
    "rabbit": ("🐰", ["a photo of a rabbit"]),
    "insect": ("🐝", ["a photo of an insect", "a photo of a bee", "a photo of a fly", "a photo of an ant"]),
    "butterfly": ("🦋", ["a photo of a butterfly"]),
    "horse": ("🐴", ["a photo of a horse"]),
    "cow": ("🐮", ["a photo of a cow"]),
    "goat": ("🐐", ["a photo of a goat"]),
    "sheep": ("🐑", ["a photo of a sheep"]),
    "monkey": ("🐒", ["a photo of a monkey"]),
    "reptile": ("🦎", ["a photo of a lizard", "a photo of a turtle", "a photo of a snake"]),
    "no animal": ("🚫", ["a photo of a plant", "a photo of an empty street", "a photo of a room", "a photo of food"]),
}
TYPE_CONFIDENT = 0.60  # only filter "same animal type" when the type guess is at least this sure

st.set_page_config(page_title="Animal ID · DINOv2", page_icon="🐾", layout="wide")


# --------------------------------------------------------------------------------------
# Models and image processing
# --------------------------------------------------------------------------------------


@st.cache_resource(show_spinner="Loading the models (first run downloads about 1 GB)...")
def get_models():
    device = pick_device()
    return Embedder(BACKBONES[MODEL_KEY], device), AnimalCropper(device, min_score=0.4), str(device)


@st.cache_resource(show_spinner=False)
def get_type_model():
    import torch
    from transformers import AutoModel, AutoProcessor

    device = pick_device()
    hf_id = BACKBONES[TYPE_MODEL_KEY].hf_id
    processor = AutoProcessor.from_pretrained(hf_id)
    model = AutoModel.from_pretrained(hf_id).to(device).eval()
    prompts = [(name, t) for name, (_, ts) in ANIMAL_TYPES.items() for t in ts]
    with torch.no_grad():
        tin = processor(text=[t for _, t in prompts], return_tensors="pt", padding=True).to(device)
        out = model.get_text_features(**tin)
        T = torch.nn.functional.normalize((out if isinstance(out, torch.Tensor) else out.pooler_output).float(), dim=-1)
    names = list(ANIMAL_TYPES)
    owner = torch.tensor([names.index(n) for n, _ in prompts], device=device)
    return processor, model, T, owner, names, device


def animal_type(img: Image.Image) -> tuple[str, float]:
    import torch

    processor, model, T, owner, names, device = get_type_model()
    with torch.no_grad():
        out = model.get_image_features(**processor(images=img, return_tensors="pt").to(device))
        v = torch.nn.functional.normalize((out if isinstance(out, torch.Tensor) else out.pooler_output).float(), dim=-1)[0]
        logits = (T @ v) * model.logit_scale.exp()
        per_type = torch.stack([torch.logsumexp(logits[owner == k], 0) for k in range(len(names))])
        probs = torch.softmax(per_type, 0)
    k = int(probs.argmax())
    return names[k], float(probs[k])


def open_upload(f) -> Image.Image:
    img = Image.open(io.BytesIO(f.getvalue()))
    return ImageOps.exif_transpose(img).convert("RGB")


def shrink(img: Image.Image, side: int = 1024) -> Image.Image:
    img = img.copy()
    img.thumbnail((side, side))
    return img


def prepare(img: Image.Image) -> dict:
    """Detect + crop the animal, then embed both the crop and the whole photo (memoised per image)."""
    memo = st.session_state.setdefault("_prep_memo", {})
    key = hashlib.sha1(img.tobytes()).hexdigest() + str(img.size)
    if key not in memo:
        if len(memo) > 64:
            memo.clear()
        memo[key] = _prepare(img)
    return memo[key]


def _prepare(img: Image.Image) -> dict:
    embedder, detector, _ = get_models()
    img = shrink(img)
    hit = detector.detect(img)
    crop = hit[0] if hit else img
    species, conf = animal_type(crop)
    e_crop, e_full = embedder.embed([crop, img])
    return {"image": img, "crop": crop, "found": bool(hit), "species": species, "det_score": conf,
            "emb_crop": e_crop, "emb_full": e_full}


def label(species: str) -> str:
    emoji = ANIMAL_TYPES.get(species, ("🐾", []))[0]
    return f"{emoji} {species.capitalize()}" if species and species != "unknown" else "🐾 Unknown animal"


# --------------------------------------------------------------------------------------
# Gallery (registered animals) on disk
# --------------------------------------------------------------------------------------


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "animal"


def load_gallery() -> list[dict]:
    animals = []
    for meta in sorted(GALLERY.glob("*/meta.json")):
        a = json.loads(meta.read_text())
        a["dir"] = meta.parent
        for p in a["photos"]:
            p["emb_crop"] = np.asarray(p["emb_crop"], dtype=np.float32)
            p["emb_full"] = np.asarray(p["emb_full"], dtype=np.float32)
        animals.append(a)
    return animals


def _photo_record(folder: Path, prep: dict, k: int) -> dict:
    stem = f"{datetime.now():%Y%m%d%H%M%S}-{k:02d}"
    prep["image"].save(folder / f"{stem}.jpg", quality=90)
    prep["crop"].save(folder / f"{stem}_crop.jpg", quality=90)
    return {"file": f"{stem}.jpg", "crop": f"{stem}_crop.jpg", "species": prep["species"], "det_score": prep["det_score"],
            "emb_crop": prep["emb_crop"].tolist(), "emb_full": prep["emb_full"].tolist()}


def majority_species(preps: list[dict]) -> str:
    c = Counter(p["species"] for p in preps if p["species"] and p["species"] != "no animal")
    return c.most_common(1)[0][0] if c else "unknown"


def save_animal(name: str, preps: list[dict], species: str | None = None) -> None:
    folder = GALLERY / f"{slug(name)}-{uuid.uuid4().hex[:6]}"
    (folder / "photos").mkdir(parents=True)
    photos = [_photo_record(folder / "photos", p, k) for k, p in enumerate(preps)]
    meta = {"name": name, "species": species or majority_species(preps), "created": datetime.now().isoformat(timespec="seconds"),
            "photos": photos}
    (folder / "meta.json").write_text(json.dumps(meta))


def add_photos(animal: dict, preps: list[dict]) -> None:
    meta_path = animal["dir"] / "meta.json"
    meta = json.loads(meta_path.read_text())
    start = len(meta["photos"])
    meta["photos"] += [_photo_record(animal["dir"] / "photos", p, start + k) for k, p in enumerate(preps)]
    meta_path.write_text(json.dumps(meta))


def delete_animal(animal: dict) -> None:
    for f in sorted(animal["dir"].rglob("*"), reverse=True):
        f.unlink() if f.is_file() else f.rmdir()
    animal["dir"].rmdir()


# --------------------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------------------


def rank(prep: dict, animals: list[dict], use_crop: bool, same_species: bool) -> list[dict]:
    key = "emb_crop" if use_crop else "emb_full"
    q = prep[key]
    rows = []
    for a in animals:
        if (same_species and prep["det_score"] >= TYPE_CONFIDENT and prep["species"] != "no animal"
                and a["species"] not in ("unknown", prep["species"])):
            continue  # a confidently recognised cat can't be a registered dog
        sims = [float(p[key] @ q) for p in a["photos"]]
        k = int(np.argmax(sims))
        rows.append({"animal": a, "best": sims[k], "photo": a["photos"][k], "mean": float(np.mean(sims)), "sims": sims})
    return sorted(rows, key=lambda r: -r["best"])


def verdict(sim: float, accept: float, review: float) -> tuple[str, str]:
    if sim >= accept:
        return "match", "✅ Same animal"
    if sim >= review:
        return "review", "🟡 Possibly the same animal — needs a check"
    return "new", "🆕 Not a registered animal"


def photo_path(animal: dict, photo: dict, crop: bool) -> Path:
    return animal["dir"] / "photos" / (photo["crop"] if crop else photo["file"])


# --------------------------------------------------------------------------------------
# Demo data (public Multi-pose Dog Dataset, CC BY 4.0)
# --------------------------------------------------------------------------------------


def load_demo(n_registered: int = 6, n_strangers: int = 2) -> int:
    rows = list(csv.DictReader(open(DEMO_MANIFEST)))
    by: dict = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["animal_id"]][r["session"]].append(DEMO_MANIFEST.parent / r["path"])
    dogs = [a for a, s in by.items() if len(s) >= 3]
    dogs.sort(key=lambda a: -min(min(Image.open(p).size) for p in by[a][sorted(by[a])[0]]))  # sharpest first
    tests, bar = [], st.progress(0.0, "Registering demo dogs...")
    for i, a in enumerate(dogs[:n_registered]):
        sess = sorted(by[a])
        reg = [p for s in sess[:2] for p in by[a][s]][:4]  # register from 2 sessions = several angles
        save_animal(f"Demo dog {i + 1}", [prepare(load_image(p)) for p in reg], species="dog")
        tests += [{"path": str(p), "truth": f"Demo dog {i + 1}"} for s in sess[2:] for p in by[a][s][:1]]
        bar.progress((i + 1) / n_registered, f"Registered Demo dog {i + 1}")
    for j, a in enumerate(dogs[n_registered:n_registered + n_strangers]):
        tests += [{"path": str(p), "truth": f"Unregistered dog {j + 1}"} for s in sorted(by[a])[:2] for p in by[a][s][:1]]
    (GALLERY / "_demo_tests.json").write_text(json.dumps(tests))
    bar.empty()
    return n_registered


# --------------------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------------------

GALLERY.mkdir(parents=True, exist_ok=True)
animals = load_gallery()

with st.sidebar:
    st.title("🐾 Animal ID")
    st.caption("Research demo · runs locally · not the live product")
    st.markdown(f"**Identity:** DINOv2-base  \n**Animal type:** OpenCLIP (LAION)  \n**Cropping:** RT-DETRv2  \n"
                f"**Registered animals:** {len(animals)}")
    st.divider()
    st.subheader("Decision thresholds")
    accept = st.slider("Same animal if similarity ≥", 0.50, 0.99, DEFAULT_ACCEPT, 0.01)
    review = st.slider("Needs a check if similarity ≥", 0.30, accept, min(DEFAULT_REVIEW, accept), 0.01)
    st.caption("Defaults were calibrated on 191 public dogs so that no wrong dog was ever accepted.")
    use_crop = st.toggle("Crop the animal before matching", value=True,
                         help="Recommended: stops two animals photographed in the same place from looking alike.")
    same_species = st.toggle("Only compare with the same animal type", value=True)
    st.divider()
    if DEMO_MANIFEST.exists() and not any(a["name"].startswith("Demo dog") for a in animals):
        if st.button("Load demo dogs (public dataset)"):
            load_demo()
            st.rerun()

tab_id, tab_reg, tab_angles, tab_gal, tab_how = st.tabs(
    ["🔍 Identify", "➕ Register animal", "📐 Angle test", "🗂️ Registered animals", "ℹ️ How it works"])

# ---- Identify ------------------------------------------------------------------------
with tab_id:
    st.header("Who is this animal?")
    if not animals:
        st.info("No animals registered yet. Register one in **➕ Register animal**, or load the demo dogs from the sidebar.")
    src = st.radio("Photo source", ["Upload", "Camera", "Demo test photo"], horizontal=True, label_visibility="collapsed")
    probes: list[tuple[str, Image.Image]] = []
    truth = None
    if src == "Upload":
        files = st.file_uploader("Upload one or more photos", type=["jpg", "jpeg", "png", "webp", "heic"],
                                 accept_multiple_files=True, key="id_up")
        probes = [(f.name, open_upload(f)) for f in files or []]
    elif src == "Camera":
        shot = st.camera_input("Take a photo")
        if shot:
            probes = [("camera", open_upload(shot))]
    else:
        tests_file = GALLERY / "_demo_tests.json"
        if tests_file.exists():
            tests = json.loads(tests_file.read_text())
            choice = st.selectbox("Demo photo (never used for registration)", range(len(tests)),
                                  format_func=lambda i: f"Photo {i + 1}")
            probes = [(f"demo {choice + 1}", load_image(Path(tests[choice]["path"])))]
            truth = tests[choice]["truth"]
        else:
            st.caption("Load the demo dogs from the sidebar first.")

    for name, img in probes:
        prep = prepare(img)
        st.divider()
        c1, c2 = st.columns([1, 2], gap="large")
        with c1:
            st.image(prep["crop"] if use_crop else prep["image"], caption=f"{name} · what the model compares", width=300)
            st.markdown(f"### {label(prep['species'])}")
            st.caption(f"Animal type confidence: {prep['det_score']:.0%}"
                       + ("" if prep["found"] else " · animal not localised, whole photo used"))
            if truth:
                st.caption(f"Ground truth (demo only): **{truth}**")
        with c2:
            ranked = rank(prep, animals, use_crop, same_species)
            if not ranked:
                st.warning("No registered animal of this type to compare with.")
                continue
            top = ranked[0]
            code, text = verdict(top["best"], accept, review)
            second = ranked[1]["best"] if len(ranked) > 1 else None
            if code == "review":
                st.markdown(f"## Possibly {top['animal']['name']} · {top['best']:.0%} match")
                st.markdown(f"**{text}** · {label(top['animal']['species'])}"
                            + (f" · {top['best'] - second:+.0%} ahead of the next animal" if second is not None else ""))
            elif code == "new":
                st.markdown(f"## {text}")
                st.markdown(f"Closest registered animal: **{top['animal']['name']}** at **{top['best']:.0%}** similarity.")
            else:
                st.markdown(f"## {top['animal']['name']} · {top['best']:.0%} match")
                st.markdown(f"**{text}** · {label(top['animal']['species'])}"
                            + (f" · {top['best'] - second:+.0%} ahead of the next animal" if second is not None else ""))
            m1, m2 = st.columns(2)
            m1.image(str(photo_path(top["animal"], top["photo"], use_crop)), width=220,
                     caption=f"Closest registered angle of {top['animal']['name']}")
            with m2:
                st.markdown("**Similarity to each registered angle**")
                for k, s in enumerate(top["sims"]):
                    st.progress(max(0.0, min(1.0, s)), f"Angle {k + 1}: {s:.0%}")
            st.markdown("**All registered animals, best angle first**")
            st.dataframe(
                [{"Animal": r["animal"]["name"], "Type": r["animal"]["species"], "Best angle %": round(r["best"] * 100),
                  "Average over angles %": round(r["mean"] * 100), "Verdict": verdict(r["best"], accept, review)[1]}
                 for r in ranked],
                hide_index=True,
                column_config={"Best angle %": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)},
            )
            if code != "new" and name != "camera" and not truth:
                if st.button(f"Confirm it's {top['animal']['name']} and add this angle to its profile", key=f"add-{name}"):
                    add_photos(top["animal"], [prep])
                    st.success("Added. Future scans can match this angle too.")

# ---- Register ------------------------------------------------------------------------
with tab_reg:
    st.header("Register an individual animal")
    st.markdown("Upload **3–8 photos of the same animal from different angles** (front, side, back, sitting, standing). "
                "More angles means it can be recognised from more directions.")
    with st.form("register", clear_on_submit=True):
        name = st.text_input("Animal's name", placeholder="e.g. Bella")
        files = st.file_uploader("Photos from different angles", type=["jpg", "jpeg", "png", "webp", "heic"],
                                 accept_multiple_files=True)
        ok = st.form_submit_button("Register", type="primary")
    if ok:
        if not name or not files:
            st.error("Add a name and at least one photo.")
        else:
            with st.spinner("Detecting and fingerprinting each angle..."):
                preps = [prepare(open_upload(f)) for f in files]
            save_animal(name, preps)
            st.success(f"Registered **{name}** ({label(majority_species(preps))}) from {len(preps)} photos.")
            cols = st.columns(min(len(preps), 6))
            for k, p in enumerate(preps):
                cols[k % len(cols)].image(p["crop"], caption=label(p["species"]), width=150)
            if any(not p["found"] for p in preps):
                st.warning("The animal could not be localised in some photos; the whole photo was used for those.")

# ---- Angle test ----------------------------------------------------------------------
with tab_angles:
    st.header("How similar is one animal across angles?")
    st.markdown("Upload several photos of **one** animal. The table shows how similar each angle is to every other angle.")
    files = st.file_uploader("Photos of the same animal", type=["jpg", "jpeg", "png", "webp", "heic"],
                             accept_multiple_files=True, key="angles")
    if files and len(files) >= 2:
        with st.spinner("Comparing angles..."):
            preps = [prepare(open_upload(f)) for f in files]
        key = "emb_crop" if use_crop else "emb_full"
        E = np.stack([p[key] for p in preps])
        M = E @ E.T
        cols = st.columns(min(len(preps), 8))
        for k, p in enumerate(preps):
            cols[k % len(cols)].image(p["crop"] if use_crop else p["image"], caption=f"Angle {k + 1} · {label(p['species'])}", width=130)
        names = [f"Angle {k + 1}" for k in range(len(preps))]
        st.dataframe({"": names, **{n: [f"{M[i, j]:.0%}" for i in range(len(preps))] for j, n in enumerate(names)}},
                     hide_index=True)
        off = M[~np.eye(len(preps), dtype=bool)]
        a, b, c = st.columns(3)
        a.metric("Average match between angles", f"{off.mean():.0%}")
        b.metric("Lowest (hardest pair)", f"{off.min():.0%}")
        c.metric("Pairs above the 'same animal' line", f"{(off >= accept).mean():.0%}")
        st.caption("Pairs below the line are angles that look too different on their own, so register those angles too.")
        if animals:
            st.markdown("**Each angle identified against the registered animals**")
            out = []
            for k, p in enumerate(preps):
                r = rank(p, animals, use_crop, same_species)
                out.append({"Photo": names[k], "Animal type": p["species"] or "not detected",
                            "Best match": r[0]["animal"]["name"] if r else "-", "Similarity %": round(r[0]["best"] * 100) if r else 0,
                            "Verdict": verdict(r[0]["best"], accept, review)[1] if r else "-"})
            st.dataframe(out, hide_index=True,
                         column_config={"Similarity %": st.column_config.ProgressColumn(format="%d%%", min_value=0, max_value=100)})
        with st.form("reg_angles"):
            nm = st.text_input("Register these angles as a new animal named")
            if st.form_submit_button("Register") and nm:
                save_animal(nm, preps)
                st.success(f"Registered {nm}.")
    elif files:
        st.caption("Add at least two photos.")

# ---- Gallery -------------------------------------------------------------------------
with tab_gal:
    st.header("Registered animals")
    if not animals:
        st.caption("Nothing registered yet.")
    for a in animals:
        with st.expander(f"{label(a['species'])} · **{a['name']}** · {len(a['photos'])} angles"):
            cols = st.columns(min(len(a["photos"]), 8))
            for k, p in enumerate(a["photos"]):
                cols[k % len(cols)].image(str(photo_path(a, p, True)), width=110)
            more = st.file_uploader("Add more angles", type=["jpg", "jpeg", "png", "webp", "heic"],
                                    accept_multiple_files=True, key=f"more-{a['dir'].name}")
            c1, c2 = st.columns(2)
            if more and c1.button("Add these angles", key=f"addm-{a['dir'].name}"):
                add_photos(a, [prepare(open_upload(f)) for f in more])
                st.rerun()
            if c2.button("Delete this animal", key=f"del-{a['dir'].name}"):
                delete_animal(a)
                st.rerun()

# ---- How it works --------------------------------------------------------------------
with tab_how:
    st.header("How it works")
    st.markdown(f"""
1. **Find and name the animal.** RT-DETRv2 finds the animal and crops it. OpenCLIP names its type (dog, cat, bird, rodent,
   insect, ...) by comparing the crop with descriptions like "a photo of a dog".
2. **Fingerprint it.** DINOv2-base turns the crop into 768 numbers that describe how this animal looks.
3. **Compare.** The new fingerprint is compared with **every registered angle** of every animal. The best angle counts, so a side view
   is matched against the registered side view.
4. **Similarity %** is the cosine similarity × 100. Similar fingerprints score close to 100%.
5. **Decision.** ≥ {accept:.0%} → same animal · ≥ {review:.0%} → needs a check · lower → new animal.

**Limits.** Individual recognition works best on cats and dogs with distinctive looks. Very similar animals (two black cats, two pigeons)
can score high, which is why the "needs a check" band exists. If the animal can't be localised (common for insects and small rodents),
the whole photo is used.

**Device:** {get_models()[2]} · photos are stored only in `tools/model-eval/data/app_gallery/`.
""")
    if DEMO_MANIFEST.exists():
        st.caption("Demo photos: Multi-pose Dog Dataset, Mendeley Data, CC BY 4.0.")
