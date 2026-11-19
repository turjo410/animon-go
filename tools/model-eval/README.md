# tools/model-eval

Offline evaluation harness for Animon GO's two model problems. **Research tooling only; nothing here ships in the app.**

- `identity_bench.py`: "Is this the same cat or dog?" Ranks frozen embedding models (DINOv2, SigLIP 2, OpenCLIP), with or without animal cropping.
- `classify_bench.py`: "Which family is this, or no confident match?" Ranks zero-shot models, with ImageNet classifiers included as evaluation-only baselines.

Why these models, and which ones are banned: [`docs/research/model-license-screen.md`](../../docs/research/model-license-screen.md).
Where this fits in the overall plan: [`docs/research/model-evaluation-plan.md`](../../docs/research/model-evaluation-plan.md).

## Setup

You need [`uv`](https://docs.astral.sh/uv/); it fetches Python 3.12 itself.

```sh
cd tools/model-eval
uv sync
```

Model weights download from Hugging Face on first use (about 3 GB in total) and are cached in `~/.cache/huggingface`. It runs on Apple-silicon GPU (MPS), CUDA or CPU.

## 1. Smoke test (checks that everything runs, not real-world accuracy)

```sh
uv run make_smoke_data.py                      # SYNTHETIC: internet photos re-augmented into fake "sessions"
uv run make_manifest.py data/_smoke/identity
uv run identity_bench.py --manifest data/_smoke/identity/manifest.csv --label "SYNTHETIC SMOKE TEST"
uv run classify_bench.py --data data/_smoke/classify --label "SYNTHETIC SMOKE TEST"
```

## 2. Real evaluation

**Identity data:** one folder per real animal. File names follow `<session>__<phone>__<n>.<ext>`.

```text
data/identity/
  cat/cat-01-milo/s1__iphone13__001.heic
  cat/cat-01-milo/s2__pixel7__001.jpg
  dog/dog-01-rex/...
```

```sh
uv run make_manifest.py data/identity           # then optionally fill the `location` / `role` columns
uv run identity_bench.py --manifest data/identity/manifest.csv --label "pilot data v1"
```

What the identity benchmark does:
- **Registered vs. unfamiliar:** 5 animals per species are held out as *unfamiliar* (`--unfamiliar-per-species`, seeded), or set them yourself with the `role` column.
- **Enrollment:** each registered animal is enrolled from its **earliest session only**. Its later sessions are the probes.
- **Thresholds:** animals are split in half. The thresholds (accept, and send-to-review) are chosen on the CALIB half and **frozen** before scoring the TEST half.
- **Failures:** "no animal detected" counts as a failure; nothing is dropped.

Options:

| Option | Effect |
|---|---|
| `--accept-margin 0.05` | Raises the accept bar: fewer automatic matches, more sent to operator review |
| `--crop none\|rtdetr\|both` | Whole photo vs. a crop around the detected animal (RT-DETRv2, Apache-2.0) |
| `--gallery-agg max\|mean` | Match against the best single enrollment photo, or the averaged prototype |

**Classification data:** `data/classify/{feline,canine,avian,rodent,insect,none}/*.jpg`

```sh
uv run classify_bench.py --data data/classify --label "pilot data v1"
```

## 3. Public pre-checks (real photos, before our own collection exists)

These give real-photo numbers earlier than our own collection can. They are easier and less representative than our own set (plan step 3), so treat them as a filter, not as evidence for the pilot. All images stay in `data/`, which git ignores, and are used only for internal evaluation.

**Family classification: iNaturalist.**
- **What it fetches:** real phone photos of city animals, including pigeons, house crows, mynas, sparrows, rats, mice, palm and grey squirrels, bees, flies, butterflies, ladybirds, dragonflies, mosquitoes, ants, cats, dogs and foxes.
- **Licence:** only CC0 or CC-BY photos are downloaded, and attribution is recorded in `ATTRIBUTION.csv`.
- **The "none" class:** plant and fungus photos. Rooms, streets, toys and screens are not covered.

```sh
uv run fetch_public_classify.py
uv run classify_bench.py --data data/public_classify --label "iNaturalist pre-check"
```

**Identity: Multi-pose Dog Dataset.**
- **Source:** Mendeley Data, [doi:10.17632/v5j6m8dzhv.1](https://data.mendeley.com/datasets/v5j6m8dzhv/1), CC BY 4.0. 191 dogs, 1,656 pre-cropped photos taken with several cameras.
- **Caveats:** sequences may come from the same day, and some dogs wear distinctive clothing. No public cat set with a clear licence has been found yet.

```sh
mkdir -p data/public_identity/mpdd_raw && cd data/public_identity/mpdd_raw
curl -L -o MPDD.zip "https://data.mendeley.com/public-files/datasets/v5j6m8dzhv/files/05d1d583-faf6-410d-89a5-a6b1134b6e5e/file_downloaded"
unzip -q MPDD.zip -d x && cd ../../..
uv run import_mpdd.py
uv run identity_bench.py --manifest data/public_identity/mpdd_manifest.csv --crop none \
    --unfamiliar-per-species 64 --label "MPDD public pre-check"
```

## Outputs

Everything goes to `results/<run>/`:
- `summary.md`: the table to read
- `summary.json`
- `probes.csv` / `predictions.csv`: one row per image, for digging into errors
- `sweep_*.csv` (identity only): correct-accept / wrong-animal / unfamiliar-accept rates at every threshold

`results/` and `data/` are git-ignored because they reference participants' photos. Copy only `summary.md` into `docs/research/results/` if you want a record in the repo.

## Caveats

- **Latency here is laptop latency.** Phone latency is measured separately, on-device (plan step 6).
- **Sample size:** with about 30 animals, "0 wrong matches" is preliminary evidence, not proof.
- **ImageNet coverage:** the classes have no rat, mouse, pigeon, sparrow or crow, which is why the ImageNet baselines score poorly on Rodent and Avian.
- **Regenerating the family map:** `imagenet_family_map.json` is generated from WordNet. Rebuild it with `uv sync --extra wordnet && uv run build_imagenet_map.py`.

## 4. Animal ID demo website (Streamlit)

Register individual animals from several angles, then identify new photos. It shows the animal type, the best-matching individual, its similarity % and a verdict:

```
uv run --extra app streamlit run app/animal_id_app.py
```

- **Identity:** DINOv2-base. **Animal type:** zero-shot OpenCLIP (LAION). **Cropping:** RT-DETRv2. All are cleared in the licence screen; the first run downloads about 1 GB of models.
- Registered animals are stored in `data/app_gallery/` (git-ignored). Photos never leave the machine.
- **Load demo dogs** (sidebar) registers 6 public MPDD dogs and provides held-out test photos, including 2 unregistered dogs.
- It's a research demo, not the live product.
