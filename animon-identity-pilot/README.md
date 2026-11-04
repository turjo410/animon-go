# Animon GO — Animal Identity Pilot

A bounded experiment, not the main product: can we reliably recognize the same real cat or dog across different players, phones, and days — without training our own model?

Full context: [`../docs/research/identity-pilot-setup-plan.md`](../docs/research/identity-pilot-setup-plan.md) and [`../docs/research/animal-identification-rnd.md`](../docs/research/animal-identification-rnd.md). Governing principles: [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (this pilot) and [`../.specify/memory/constitution.md`](../.specify/memory/constitution.md) (main product — takes precedence on privacy/identity).

## Status

Spec Kit initialized; first feature spec drafted at [`specs/001-cats-dogs-identity-pilot/spec.md`](specs/001-cats-dogs-identity-pilot/spec.md). No application code yet — next steps are `/speckit-plan` and `/speckit-tasks` (run as `animon-identity-pilot:speckit-plan` / `animon-identity-pilot:speckit-tasks` if your agent scopes skills by directory).

## Planned stack (not yet scaffolded)

TypeScript + Next.js, Supabase Auth + Postgres, a provider adapter (`mock` + `petify`), Vitest + Playwright. See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md#5-identity-pilot-architecture-animon-identity-pilot).

## Relationship to the main product

This pilot does not ship inside `apps/mobile`. It produces a go/no-go decision (see [`../docs/ROADMAP.md`](../docs/ROADMAP.md) Phase 2/3) that the main product later acts on. Treat its output as evidence, not as a dependency the mobile MVP waits on.
