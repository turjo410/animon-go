# 2026-11-08 — Model licence screen and offline evaluation harness

## What

- **Licence filter for every ML model.** Every ML model considered for Animon GO, whether it runs on-device or on the server, must pass the licence screen in [`docs/research/model-license-screen.md`](../research/model-license-screen.md) before it is benchmarked. That screen was checked independently by Claude Code and Codex.
- **Ruled out for shipping:**
  - Ultralytics YOLO (AGPL-3.0; allowed only with a paid Enterprise licence)
  - Apple MobileCLIP / MobileCLIP2 (research-only weights)
  - OpenAI CLIP weights (no stated weight licence; deployment excluded by the model card)
  - MiewID (hosted-only)
  - MegaDetector v5 and the AGPL MegaDetector v6 variants
- **Evaluation-only:**
  - ImageNet-trained timm/torchvision weights (ImageNet's non-commercial terms are assumed to carry over)
  - MegaDescriptor (CC-BY-NC)
  - PetFace (non-commercial research)
- **Needs a legal read before use:** DINOv3 (custom licence).
- **Offline harness:** a Python harness lives at [`tools/model-eval/`](../../tools/model-eval/). It is research tooling and is **not** a product stack choice; nothing in it ships. It ranks shortlisted models for both family classification and individual identity, using the evaluation shape of setup plan §7.

## Why

- A model that can't legally ship in a commercial closed-source game is not a candidate, however accurate it is. Screening first avoids wasted benchmarking and avoids a forced re-architecture late in the project.
- The SRS accuracy and latency targets (NFR-ACC-1 88%, NFR-LAT-1 1.5 s) are unvalidated. They need a repeatable measurement, not a vendor claim.
- The screen also surfaced a coverage problem: ImageNet-1k has no rat, mouse, pigeon, sparrow or crow classes, so ImageNet-only classifiers are structurally weak for the Rodent and Avian families. That favours zero-shot SigLIP 2 / OpenCLIP, or ML Kit, for family classification, subject to measurement.

## Alternatives considered

- **Benchmark first, check licences later.** Rejected: it risks choosing a model that can't ship. YOLO, the default choice for most detection tutorials, is AGPL.
- **Buy an Ultralytics Enterprise licence.** Deferred: it is an annual cost, and Apache-licensed detectors (RT-DETRv2, D-FINE COCO-only, the MIT/Apache MegaDetector v6 variants) cover the need.
- **Evaluate inside the Next.js pilot instead of Python.** Rejected for this step: the models and their tooling are native to Python, and the harness must run before any pilot app exists.

## Scope and limits

- **The screen is not legal advice.** Before anything ships, the exact checkpoint (repo, revision, hash) and its licence must be recorded in the model-selection decision record. That record is plan step 7.
- **Synthetic numbers prove nothing.** Smoke-test numbers from synthetic data aren't evidence. Real selection waits for the photo collection (plan step 3) and the on-device check (plan step 6).
