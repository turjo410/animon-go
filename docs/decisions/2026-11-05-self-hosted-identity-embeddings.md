# 2026-11-05 — Self-hosted identity embeddings replace Petify as the default live provider

## What

The identity pilot's default **live** implementation is no longer Petnow's Petify (a paid, per-pet commercial identification API). Instead:

- Image embeddings come from a **frozen, permissively-licensed pretrained vision model** (DINOv2, Apache 2.0) — no new backbone is trained.
- Embeddings are stored and matched **ourselves**, in Supabase Postgres using the `pgvector` extension (cosine-similarity nearest-neighbor search).
- The decision pipeline (capture → retrieve candidates → estimate plausibility → re-rank conservatively → preserve uncertainty → update carefully) is unchanged from [`docs/research/animal-identification-spatiotemporal-inference-summary.pdf`](../research/animal-identification-spatiotemporal-inference-summary.pdf) — only who runs the matching changes.
- v1 inference runs via a **hosted inference API call** to the extractor (zero infrastructure to manage); a small self-hosted CPU/ONNX service is an allowed later swap without changing the provider interface or the database schema.

The identity-provider interface still supports a `mock` implementation and remains pluggable — Petify or another commercial vendor MAY be added later purely as an evaluation comparison, but is not required to ship the pilot.

## Why

- Avoids recurring per-pet cost (Petify Plus was ~US$0.75/pet/month) and vendor lock-in for a mechanic that is still unproven.
- The team wants to own this mechanism rather than depend on a third-party identification vendor.
- This is feasible for a solo developer with modest compute: no model training is required for v1 — only inference calls to an existing open-weight model. A hosted inference endpoint needs no GPU or server management at all; self-hosting the same frozen model via ONNX on a small CPU box is the next-cheapest option if lower latency/cost is wanted later.

## Alternatives considered

- **Petify (status quo)** — rejected as the default: lowest integration effort, but recurring cost and vendor dependency for a mechanism the team wants to own. May still be evaluated later as a comparison point.
- **Hosted MiewID** — rejected for self-hosting: its published model-use terms restrict it to Conservation X Labs-hosted applications; not available to self-host (see [`docs/ROADMAP.md`](../ROADMAP.md) non-goals).
- **Training a custom recognition model from scratch** — rejected: the strongest academic benchmark in this space (PetFace) needed 257,484 labeled individuals to get good results; not achievable at this team's scale or data.
- **MegaDescriptor weights** — rejected for this use: CC BY-NC 4.0 license is non-commercial only, incompatible with a commercial product.

## Scope and limits

- v1 is a **frozen extractor only** — no training. A small trained projection head on top of the frozen backbone (similar in spirit to the "Open Noodle" pet model referenced in the research summary) is an allowed future step, but only once real pilot capture data exists to train and evaluate it against.
- Capabilities previously provided by Petify must now be built in-house: a guided-capture UX that produces consistent, comparable framing, and basic anti-spoof/liveness checks (rejecting a photo-of-a-photo). These are tracked as pilot implementation work, not assumed to come for free.
- Calibration and evaluation still follow the existing pilot plan: the 30-animal (15 cat / 15 dog) protocol in [`docs/research/identity-pilot-setup-plan.md`](../research/identity-pilot-setup-plan.md) §7, with thresholds frozen after calibration per the research summary's evaluation section.

## Updated accordingly

- [`animon-identity-pilot/.specify/memory/constitution.md`](../../animon-identity-pilot/.specify/memory/constitution.md) — Principle I and Technology constraints.
- [`docs/SRS.md`](../SRS.md) — §2, §4.4 (FR-130), §6 (SEC-4), §8, §9.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — §4, §5, §6, §7.
- [`docs/ROADMAP.md`](../ROADMAP.md) — non-goals.
- [`animon-identity-pilot/README.md`](../../animon-identity-pilot/README.md) and [`animon-identity-pilot/specs/001-cats-dogs-identity-pilot/spec.md`](../../animon-identity-pilot/specs/001-cats-dogs-identity-pilot/spec.md) (FR-008, Assumptions).
