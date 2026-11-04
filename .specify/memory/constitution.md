# Animon GO (mobile product) Constitution

## Core Principles

### I. Mobile-first, native product
The real product is a native mobile app (Flutter, iOS + Android) under `apps/mobile`. `animon-web` is a read-only, external reference prototype used to validate game design — it is never the implementation target and is never edited from this repository. Features are designed for touch, camera, and GPS as first-class inputs, not ported unchanged from a browser interaction model.

### II. Spec before code
No feature is implemented without a Spec Kit pass: `/speckit-specify` → (`/speckit-clarify` if ambiguous) → `/speckit-plan` → `/speckit-tasks` → (`/speckit-analyze` if non-trivial) → `/speckit-implement`. The baseline documents (`docs/BRD.md`, `docs/PRD.md`, `docs/SRS.md`, `docs/ARCHITECTURE.md`) constrain what a spec may assume; a spec that needs to contradict them requires a recorded decision in `docs/decisions/`, not a silent drift.

### III. Identity ≠ familiarity (NON-NEGOTIABLE)
The default product NEVER claims biometric identification of an animal. "Familiarity" (family + time + approximate-location heuristics) is the only default collection signal. True individual recognition exists solely inside the explicitly-labeled, bounded identity pilot (`animon-identity-pilot`), which must itself always distinguish mock results from live provider results in every stored record and every UI surface.

### IV. Server is the authority for anything valuable
Currency (essence), XP, collection claims, and identity-pilot claims are validated server-side (Supabase). The mobile client renders and caches; it is never the sole source of truth for a reward-affecting action. Reward-affecting operations are idempotent against retries and duplicate callbacks.

### V. Exactly one claim per real animal identity
Where individual identity is established (identity pilot, and any future integration), at most one active collection claim exists per verified animal, enforced by a database constraint — not application logic alone. Two players encountering the same registered animal must not both receive exclusive claims.

### VI. Privacy and consent are launch-blocking, not a retrofit
No raw captured image is persisted beyond what a feature's spec explicitly discloses before capture. Location is opt-in and stored approximate/rounded, never exposed publicly. Provider credentials live server-side only. No public beta ships without a reviewed consent and retention policy covering bystanders and animal owners.

### VII. Small, evidence-driven scope (NON-NEGOTIABLE)
No custom ML model training, no AR/engine build-out, and no multiplayer/PvP until the mobile core loop and the identity pilot each produce evidence that justifies the next investment. The project already walked back one over-scoped native/AR concept into a shippable alpha once (`animon-web`); do not repeat that mistake in the other direction by over-building before validating.

## Technology constraints

- **Mobile:** Flutter (Dart), targeting iOS and Android from one codebase. Changing this requires a decision record in `docs/decisions/`.
- **Backend:** Supabase (Postgres, Auth, Storage, Edge Functions). Postgres is required specifically because exclusive-claim and idempotency rules need real relational constraints and transactions.
- **Identity pilot:** Next.js (TypeScript) + Supabase, with a provider interface (`mock` always available; `petify` as the first live implementation) — scoped and governed separately per `animon-identity-pilot/.specify/memory/constitution.md` and `docs/research/identity-pilot-setup-plan.md`.
- **Out of bounds:** `twntis-film/` is unrelated and must never be read, referenced, or modified from this project.

## Development workflow

1. Baseline docs (`docs/BRD.md`, `docs/PRD.md`, `docs/SRS.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`) set direction and must stay internally consistent.
2. Each feature gets its own `specs/<feature>/` via `/speckit-specify`, tracing back to one or more `FR-xxx`/`NFR-xxx` IDs in `docs/SRS.md` where applicable.
3. Significant, hard-to-reverse decisions (stack, provider commitments, scope cuts) are recorded in `docs/decisions/` before or immediately after being made.
4. Non-functional targets inherited from the original concept (88% classification accuracy, 1.5s latency) are treated as unvalidated until measured on real target devices and recorded — never claimed as already true.

## Governance

This constitution supersedes ad hoc practice for the mobile product (`apps/mobile`) and its shared backend. It does not govern `animon-identity-pilot`, which maintains its own constitution reflecting its narrower, pilot-specific principles (no model training, server-verified results, mock/live distinguishability). Amendments here require an entry in `docs/decisions/` describing what changed and why. Where this constitution and `docs/BRD.md`/`docs/SRS.md` disagree, treat the disagreement as a bug to resolve deliberately, not a signal to follow either document blindly.

**Version**: 1.0.0 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-05
