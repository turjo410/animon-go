# Animon GO — Animal Identity Pilot Constitution

Scope: this constitution governs only `animon-identity-pilot/`, a bounded experiment, not the main product. See `../.specify/memory/constitution.md` for the mobile product's constitution and `../docs/research/identity-pilot-setup-plan.md` for the full setup plan this was seeded from.

## Core Principles

### I. No custom model training
This pilot evaluates existing, provider-hosted individual-recognition services (starting with Petnow's Petify). It does not train or host a custom recognition model. If no existing provider is sufficient, that is a documented outcome, not a reason to start training one.

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
Prefer the smallest implementation that can produce a trustworthy evaluation: one application, one provider adapter interface (mock + Petify), one evaluation protocol. Expansion (more species, more providers) only follows evidence from this pilot.

## Technology constraints

- TypeScript + Next.js for the capture/result/review application and provider server routes.
- Supabase Auth + Postgres for accounts and shared, constrained records (exclusive claims use a database constraint, not application logic alone).
- Vitest + Playwright + Postgres integration tests for decision rules, retries, authorization, concurrent claims, and the capture handoff.
- pnpm, linting, type checking, and CI for reproducibility.
- No GPU, no vector database — this is a provider-backed pilot, not a model-hosting project.

## Governance

Amendments require updating this file and noting the change in `../docs/decisions/`. This constitution does not override the main product constitution (`../.specify/memory/constitution.md`); where the two would conflict, the main product constitution's privacy and identity principles (its Principle III and VI) take precedence, since this pilot's output must be safe to integrate into that product.

**Version**: 1.0.0 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-05
