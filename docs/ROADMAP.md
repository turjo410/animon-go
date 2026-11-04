# Roadmap — Animon GO

| | |
|---|---|
| **Document owner** | Product |
| **Status** | Draft |
| **Last updated** | 2026-11-05 |
| **Related** | [BRD](BRD.md) · [PRD](PRD.md) · [SRS](SRS.md) · [Architecture](ARCHITECTURE.md) |

Phased to de-risk the two biggest unknowns first: *does the mobile core loop work on real phones outdoors*, and *does real-world individual animal identification actually work*. Nothing downstream of those two should be built on faith.

## Phase 0 — Foundation (this reorganization)

- [x] Monorepo structure, `.gitignore` boundaries, BRD/PRD/SRS/Architecture drafted.
- [x] Flutter app scaffolded at `apps/mobile`.
- [x] Spec Kit initialized at repo root (mobile product) and inside `animon-identity-pilot/`.
- [x] Constitutions authored for both the mobile product and the identity pilot.
- [x] First `/speckit-specify` pass on the MVP core loop (`specs/001-mobile-core-loop`).
- [x] First `/speckit-specify` pass on the identity pilot (`animon-identity-pilot/specs/001-cats-dogs-identity-pilot`).
- [ ] `/speckit-plan` and `/speckit-tasks` for both specs.

**Checkpoint:** a fresh checkout has working docs, a buildable (if empty) Flutter shell, and live Spec Kit scaffolding for both sub-projects.

## Phase 1 — Mobile core loop (MVP)

- Camera capture → family classification on real devices.
- GPS-opt-in familiarity (not identity).
- Variant resolution, roster, bonding/training, 3-member squad.
- Turn-based PvE battles (ported rules from `animon-web`).
- Accounts + server-validated progress via Supabase.
- Daily trail rewards, field journal.

**Checkpoint:** a tester can install the app, discover a real animal, build a squad, and win a trial — with real GPS and camera, no browser.

## Phase 2 — Identity pilot

Run per [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md), independent of Phase 1 shipping:

1. Foundation — Spec Kit artifacts, scaffold, CI, mock mode working with no credentials needed.
2. Mock workflow — capture handoff, result states, review queue, claim handling; concurrent claims can't both succeed.
3. Provider feasibility — a few guided real captures; confirm the capture flow is practical in real encounters.
4. Live integration — server-issued sessions, server-verified results, stable identity mapping.
5. Field evaluation — the 30-animal (15 cat / 15 dog) protocol; report recognition, false matches, false accepts, capture time.
6. Decision — proceed to Phase 3 integration, investigate an alternative provider, or record a no-go.

**Checkpoint:** a written pilot result sheet with a go/no-go recommendation — not a demo, a decision record.

## Phase 3 — Identity integration or recorded no-go

- If Phase 2 is a go: integrate true individual recognition as an opt-in layer on top of family-level discovery (PRD §5.2).
- If Phase 2 is a no-go: keep family-level familiarity as the permanent default; record why in `docs/decisions/`.

## Phase 4 — World features (not committed)

- Map view, real weather feed (with explicit location handling), ARKit/ARCore "awakening" overlay.
- Expanded species coverage, contingent on further identity research.
- Social/competitive features.
- Monetization model selection (see [PRD §9](PRD.md#9-monetization-deferred)).

## Explicit non-goals (near-term)

- Real-time multiplayer/PvP.
- Any species identity claim outside the bounded cats/dogs pilot.
- Self-hosting third-party biometric models without confirmed licensing (e.g., MiewID — currently restricted to Conservation X Labs-hosted use).
