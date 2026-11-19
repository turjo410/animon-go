# Identity public pre-check — Multi-pose Dog Dataset (2026-11-10)

**Data:** [Multi-pose Dog Dataset](https://data.mendeley.com/datasets/v5j6m8dzhv/1) (Mendeley, CC BY 4.0). It has 191 dogs and 1,656 pre-cropped photos from 6 cameras. Registration and probe photos always come from different camera/sequence captures.

**Setup:**
- 64 dogs (one third) are held out as *unfamiliar*: they are never registered, and the model must not match them to anyone.
- Thresholds are frozen on one half of the dogs and scored on the other half.
- Frozen models only; nothing was trained.

**Easier than our real protocol:**
- A dog's sequences may come from the same walk or day.
- Some dogs wear distinctive clothing.
- No public cat set with a clear licence was found, so cats are untested.

Treat these numbers as a filter, not evidence for the pilot.

## Results (test dogs only)

| Model | Registered from | Correct dog ranked first | Auto-match | Wrong dog | Unfamiliar accepted | Sent to review | Registered called "unfamiliar" | ms/photo (laptop) |
|---|---|---|---|---|---|---|---|---|
| **DINOv2-base** | 1 session | 79% | 18% | **0** | **0** | 55% | 8% | 28 |
| DINOv2-small | 1 session | 74% | 16% | 4 | 0 | 49% | 14% | 9 |
| SigLIP 2-base | 1 session | 72% | 9% | 0 | 1 | 61% | 9% | 39 |
| OpenCLIP B/32 | 1 session | 61% | 6% | 1 | 0 | 69% | 8% | 17 |
| DINOv2-large | 1 session | 80% | 11% | 0 | 0 | 57% | 11% | 222 |
| **DINOv2-base** | **3 sessions** | **90%** | 15% | **0** | **0** | 49% | 6% | 28 |
| DINOv2-large | 3 sessions | 93% | 15% | 0 | 0 | 49% | 6% | 222 |

The 3-session rows have fewer probe photos, because more photos went into registration. A run comparing best-photo against averaged-photo matching (3 sessions, `--gallery-agg mean`) was stopped when the machine ran low on memory, so it has no result.

## What this tells us

1. **DINOv2-base remains the right pick.** It is the most accurate of the cleared models with zero errors. SigLIP 2 and OpenCLIP rank the right dog first less often. DINOv2-small makes wrong-dog matches. DINOv2-large is about 8× slower for almost no gain.
2. **Registering from more photos helps more than a bigger model.** Going from 1 to 3 sessions lifts correct-first ranking from 79% to 90%, and cuts the share of registered dogs wrongly called "unfamiliar" from 8% to 6%. Product implication: registration should collect several angles, or let repeat sightings add to an animal's photo set over time.
3. **The bottleneck is the strict zero-error threshold.** The right dog is usually ranked first, but the similarity scores of different dogs overlap. So keeping wrong matches at zero sends about half of all scans to review. The options to try next, in order:
   - a decision rule based on the gap between the best and second-best match
   - test-time augmentation
   - the small trained projection head on top of the frozen model, which the 2026-11-05 decision record allows once real pilot data exists

Raw outputs: `tools/model-eval/results/identity-20261110-*` (git-ignored).
