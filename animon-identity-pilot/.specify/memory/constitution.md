# Animon GO — Animal Identity Pilot Constitution

Scope: this constitution governs only `animon-identity-pilot/`, a bounded experiment, not the main product. See `../.specify/memory/constitution.md` for the mobile product's constitution and `../docs/research/identity-pilot-setup-plan.md` for the full setup plan this was seeded from.

## Core Principles

### I. No training a new vision backbone
This pilot does not train a new vision model from scratch — that needs far more labeled individual-animal data than a small team can collect. It MAY use a frozen, permissively-licensed pretrained extractor (e.g., DINOv2, Apache 2.0) purely for image embeddings, with matching and decision logic self-hosted (Supabase Postgres + pgvector), not delegated to a paid third-party identification API. A small trained projection head on top of a frozen backbone is allowed only once real pilot data justifies it (see [`docs/decisions/2026-11-05-self-hosted-identity-embeddings.md`](../../docs/decisions/2026-11-05-self-hosted-identity-embeddings.md)). A commercial provider (e.g., Petify) MAY still be evaluated as a comparison point, but is no longer the default path.

### II. Server-verified results only
Every identification result — mock or live — is verified server-side before it affects any collection decision. A client-only or redirect-only result is never trusted. Repeated/duplicate callbacks must be safe (idempotent).

### III. Mock and live evidence are always distinguishable
Every stored result and every UI surface states plainly whether it came from the mock provider or a live provider call. Nothing is allowed to blur that distinction, including during demos.

### IV. Uncertain results award nothing
Uncertain, unfamiliar, or failed identification results never automatically create or award a new animal. They may enter operator review. Only a confident, verified result reuses or creates a record.

### V. One shared identity, one active claim
Each verified animal has one shared identity record and at most one active collection claim, enforced at the database level. Two testers encountering the same registered animal must not both receive exclusive claims; the second sees "already collected."

### VI. All capture attempts count
Failed, retried, and incomplete captures are recorded in evaluation data, not discarded. A pilot that only reports successes cannot support a real go/no-go decision.

### VII. Private data stays private
Participant data, real capture evidence, and ground-truth identity records are excluded from version control and from any production analytics pipeline. Provider credentials are server-side only.

### VIII. Small, reproducible implementation
Prefer the smallest implementation that can produce a trustworthy evaluation: one application, one provider adapter interface (mock + self-hosted embedding matcher), one evaluation protocol. Expansion (more species, more providers, a trained projection head) only follows evidence from this pilot.

## Technology constraints

- TypeScript + Next.js for the capture/result/review application and provider server routes.
- Supabase Auth + Postgres for accounts and shared, constrained records (exclusive claims use a database constraint, not application logic alone); Postgres **pgvector** extension for embedding storage and nearest-neighbor matching.
- Image embeddings come from a frozen, permissively-licensed pretrained extractor (e.g., DINOv2), called via a hosted inference endpoint initially; a small self-hosted CPU/ONNX service is an allowed later swap. No GPU is required for this pilot.
- Vitest + Playwright + Postgres integration tests for decision rules, retries, authorization, concurrent claims, and the capture handoff.
- pnpm, linting, type checking, and CI for reproducibility.
- No training of a new vision backbone (Principle I). A commercial provider adapter (e.g., Petify) MAY be added later purely as an evaluation comparison, behind the same provider interface as `mock` and `self-hosted`.

## Governance

Amendments require updating this file and noting the change in `../docs/decisions/`. This constitution does not override the main product constitution (`../.specify/memory/constitution.md`); where the two would conflict, the main product constitution's privacy and identity principles (its Principle III and VI) take precedence, since this pilot's output must be safe to integrate into that product.

**Version**: 1.1.0 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-05 (Principle I and Technology constraints revised — self-hosted embedding matching replaces Petify as the default path; see [`docs/decisions/2026-11-05-self-hosted-identity-embeddings.md`](../../docs/decisions/2026-11-05-self-hosted-identity-embeddings.md))
