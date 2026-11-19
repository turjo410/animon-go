# Model evaluation plan: from candidates to a model the app can use

**Prepared:** 8 November 2026
**Covers:** both model problems in Animon GO:

| | **A. Family classification** | **B. Individual identity** |
|---|---|---|
| Question | Feline / Canine / Avian / Rodent / Insect, or no confident match? | Have we seen this exact cat or dog before? |
| Runs | On the phone, in `apps/mobile` | On the server: embedding extractor plus pgvector matching (`animon-identity-pilot`) |
| Governing requirements | SRS FR-101..104, NFR-ACC-1, NFR-LAT-1; mobile spec FR-001..004 | SRS FR-130..134; pilot spec FR-002/003/008/014; setup plan §7 |
| Blocks | Phase 1 (mobile MVP) | Phase 2 go/no-go |

**Key principle:** neither model blocks starting the app. Both sit behind an interface with a `mock` implementation (SRS §2, FR-130). App work proceeds against the mock now, and the real model is plugged in once steps 4–6 below pick one.

---

## Step 1: Licence screen ✅ done

See [`model-license-screen.md`](model-license-screen.md), checked independently by Claude Code and Codex.

Outcome:
- **Identity:** DINOv2, SigLIP 2 and OpenCLIP-LAION are allowed. DINOv3 needs a legal read first.
- **Classification:** ML Kit, and zero-shot SigLIP 2 / OpenCLIP, are allowed. ImageNet-trained weights are evaluation-only.
- **Ruled out:** MobileCLIP, OpenAI CLIP weights, Ultralytics YOLO (unless you buy Enterprise), MiewID, MegaDescriptor (evaluation-only).
- **Coverage gap:** ImageNet has no rat, mouse, pigeon, sparrow or crow classes.

## Step 2: Evaluation harness ✅ done

`tools/model-eval/` is offline Python tooling that never ships. It contains:
- `identity_bench.py`: problem B. Enrolls each registered animal from its first session, probes with its later sessions, keeps unfamiliar animals held out, freezes thresholds on one half of the animals and tests on the other half, and counts every failure.
- `classify_bench.py`: problem A. Per-family thresholds are frozen on a calibration split (FR-103), then it reports false awards, coverage per family, and how often no-animal photos are correctly rejected.

Both were verified end-to-end on a **synthetic** smoke dataset. Those numbers are not evidence. Usage: [`tools/model-eval/README.md`](../../tools/model-eval/README.md).

## Step 3: Collect evaluation photos ⏭ next, needs people and animals

You can start this immediately; it's the slowest step. All photos go in `tools/model-eval/data/`, which git ignores. Get consent from pet owners, and from anyone visible in a photo.

**Identity set (B).** This is the 30-animal protocol from setup plan §7:
- **15 cats and 15 dogs.** The harness holds out 5 of each species as unfamiliar animals by default.
- **At least 2 sessions per animal on different days.** Session 1 is enrollment; the later sessions are probes.
- **2 phones and 2 photographers.** Mix them so session 2 uses a different phone and person from session 1 where possible.
- **3–5 photos per session.** Include front, three-quarter and side views, and some imperfect real-world shots (moving, partly hidden, poor light).
- **Hard cases on purpose:** look-alike pairs (two black cats, two golden retrievers), and the same animal photographed in different places.
- **File naming:** `data/identity/<species>/<animal>/<session>__<phone>__<n>.jpg`. HEIC straight from an iPhone is fine.
- **Locations:** fill in the `location` column of the generated manifest. It enables the background-leakage check (do wrong matches share a backdrop?).

**Classification set (A).** As a starting size:
- At least **50 photos per family** for feline, canine, avian, rodent and insect, taken outdoors at realistic distances.
- Make sure the set includes pigeons, sparrows, crows, rats, mice, squirrels, and flies or mosquitoes.
- At least **100 `none` photos:** empty streets and rooms, plants, plush toys, animal statues, an animal photo shown on a screen, and people.
- **File layout:** `data/classify/<label>/*.jpg`

## Step 4: Agree pass/fail criteria *before* running ⏭ decide now

These are proposed numbers; change them, but write them down before you see any results (setup plan §7):

| Metric | Proposed bar | Why |
|---|---|---|
| B: wrong-animal awards on test animals | **0** | Any wrong-animal award blocks expansion (setup plan §7) |
| B: unfamiliar animals accepted on test | **0** | Otherwise a new animal gets merged into someone else's claim |
| B: correct automatic matches for registered animals | ≥ 60% | Below this, the review queue does most of the work |
| B: correct match or sent to review | ≥ 90% | Registered animals mustn't be called "unfamiliar" (that creates duplicate enrolments) |
| A: false awards (wrong family, or a creature awarded for a `none` photo) | ≤ 1% | FR-103: soft fail is the safe outcome |
| A: confident coverage for Feline, Canine and Avian | ≥ 80% each | Core families must feel reliable |
| A: confident coverage for Rodent and Insect | measure and report | Harder classes; decide afterwards whether launch needs them (PRD scope) |
| A: on-device latency (step 6), low-end Android reference phone | ≤ 1.5 s, capture to result | NFR-LAT-1, still unvalidated |

## Step 5: Run the offline benchmarks and shortlist

```sh
cd tools/model-eval
uv run make_manifest.py data/identity
uv run identity_bench.py --manifest data/identity/manifest.csv --label "pilot data v1"
uv run classify_bench.py --data data/classify --label "pilot data v1"
```

- **Identity:** keep a candidate only if WRONG animal = 0 and FALSE accept = 0. Among those, prefer more correct matches and fewer uncertain results. If none pass, rerun with `--accept-margin 0.05`. That makes the system more cautious and sends more results to review; check whether the review share is acceptable. If DINOv2 is clearly weak, that is the point to get DINOv3's licence read and add it.
- **Classification:** shortlist the best zero-shot model to compare against ML Kit in step 6. The ImageNet baselines are only a reference; they can't ship.
- Save each run's `summary.md` (it contains no photos) in `docs/research/results/` for the record.

## Step 6: On-device and server checks (where the app work starts)

**A. Classification on the phone.** Do this as the first implementation tasks of the mobile spec (via `/speckit-plan` for `specs/001-mobile-core-loop`):
1. Define a `FamilyClassifier` interface in `apps/mobile/lib/features/exploration/`, plus a `MockFamilyClassifier`. All UI and game-loop work can go ahead against the mock.
2. Implementation 1: **ML Kit image labeling** through the `google_mlkit_image_labeling` Flutter plugin, with its labels mapped to the 5 families.
3. Implementation 2: **the shortlisted zero-shot image tower** (step 5), exported to TFLite/LiteRT for Android and Core ML or TFLite for iOS. The text prompts are embedded once offline and bundled as a small constant matrix. Try int8 quantization, then re-check accuracy afterwards.
4. Build a small debug-only screen that runs the same photo set through both, and measures **capture-to-result latency, app-size increase and peak memory** on a low-end Android reference phone and one iPhone.
5. Pick the implementation that meets step 4's bars. Write the measured numbers into SRS NFR-ACC-1 and NFR-LAT-1, replacing the unvalidated 88% / 1.5 s.

**B. Identity on the server.**
1. Run the winning embedding model as a hosted inference endpoint, which needs no GPU management (decision 2026-11-05). Measure p50/p90 latency for one call from a phone on mobile data, and the cost per call.
2. Optionally compare an ONNX export on a small CPU server.
3. Copy the frozen thresholds from step 5 into the pilot's configuration. They are fixed and must not be re-tuned on field data (setup plan §7).

## Step 7: Record the decision

Write `docs/decisions/<date>-model-selection.md` covering:
- the chosen model for A and for B
- the exact checkpoint: repo, revision and file hash
- the licence obligations: which notice files to bundle
- the measured numbers against step 4's bars
- what was rejected and why

Update the SRS NFRs, and `docs/ARCHITECTURE.md` §7.

## Step 8: Feed into Spec Kit and build

1. **Mobile MVP:** run `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement` for `specs/001-mobile-core-loop`. The classifier is one task behind the `FamilyClassifier` interface; everything else (roster, variants, battles, Supabase) doesn't depend on which model wins.
2. **Identity pilot:** run the same sequence for `animon-identity-pilot/specs/001-cats-dogs-identity-pilot`. Build mock mode first (Phase 2.1–2.2), then plug in the self-hosted provider with step 5's thresholds.
3. **Field evaluation:** run the real pilot (Phase 2.5). The harness can re-score the pilot's exported photos the same way, so the offline results and the field results stay comparable.

## What is done, what is next

| Step | Status | Who / what is needed |
|---|---|---|
| 1. Licence screen | ✅ | — |
| 2. Harness | ✅ (smoke-tested) | — |
| 3. Photo collection | ⏭ | Consenting pet owners, 2 phones, 2 photographers, ~2 weeks |
| 4. Pass/fail bars | ⏭ | Product decision: confirm or edit the table above |
| 5. Offline benchmark | blocked by 3 | about 1 hour of compute on a laptop |
| 6. Device and server checks | can start against the mock now; real numbers need 5 | Flutter work through Spec Kit, plus a low-end Android test phone |
| 7. Decision record | after 6 | — |
| 8. Build | the mock-backed parts can start now | `/speckit-plan` for both specs |
