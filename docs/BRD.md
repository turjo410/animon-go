# Business Requirements Document (BRD) — Animon GO

| | |
|---|---|
| **Document owner** | Product |
| **Status** | Draft — foundational, for review |
| **Last updated** | 2026-11-05 |
| **Related** | [PRD](PRD.md) · [SRS](SRS.md) · [Architecture](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) |

## 1. Purpose

Define the business case, scope, and success criteria for **Animon GO**, a location-based mobile game in which players discover real animals in the world, have them "awaken" into collectible elemental creatures (Animon), train and bond with a squad, and battle in PvE trials. This document governs business intent; the [PRD](PRD.md) governs product behavior and the [SRS](SRS.md) governs system requirements.

## 2. Background

Animon GO exists today as two separate artifacts in this workspace:

- **`animon-web/`** — a browser-based alpha (React + TypeScript + Vite) that proved the core discover → classify → collect → bond → battle loop using a generic TensorFlow.js image classifier. It is a **reference prototype only** — not the product being built, and not touched by this reorganization.
- **`docs/research/`** — prior R&D on real-world individual animal identification (the long-term differentiator vs. generic "scan and get a monster" mechanics), recommending a staged pilot using Petnow's Petify service for cats/dogs before committing to a provider.

The real product is a **native mobile application** (Flutter, iOS + Android) in the spirit of Pokémon GO: outdoor exploration, camera-based discovery, GPS-aware encounters, and social/competitive collection — not a browser app.

## 3. Business objectives

| # | Objective | Why it matters |
|---|---|---|
| BO-1 | Ship a mobile MVP that proves the discover → collect → bond → battle loop works on real phones, with real GPS and camera, to real testers. | The web alpha validated the loop in a browser; it has not validated it as a mobile, outdoor, camera-driven experience. |
| BO-2 | Validate whether real-world individual animal recognition (not just species/family classification) is technically and economically viable, via the identity pilot. | This is the product's core differentiator from "point camera at anything, get a random monster." Unvalidated today. |
| BO-3 | Establish a sustainable collection/ownership model (one shared identity per real animal, one active claim) that works across many concurrent players. | Prevents duplicate claims and griefing; required before any public collection feature. |
| BO-4 | Keep player and animal-subject privacy and safety defensible from day one (no biometric claims, consent-aware capture, minimal retention). | Camera + location + animals-in-public data is sensitive; this must not become a retrofit. |
| BO-5 | Keep the engineering surface small enough for a small team to actually ship. | Previous conceptual spec implied a much heavier native AR/engine build; the team adapted once already (to web) to stay shippable. |

## 4. Stakeholders

| Stakeholder | Interest |
|---|---|
| Product owner | Overall direction, scope, go/no-go calls on provider pilots |
| Engineering (mobile — Flutter) | Build and ship `apps/mobile` |
| Engineering (identity pilot) | Validate animal recognition via `animon-identity-pilot` |
| Players (end users) | A fun, trustworthy, low-friction collection game |
| Animal subjects' owners / bystanders | Not photographed or tracked without meaningful consent and minimal retention |
| Future provider partners (e.g., Petnow/Petify) | Commercial terms, API stability, licensing |

## 5. Scope

### 5.1 In scope (this reorganization)

- A professional monorepo layout for the real mobile product, its documentation, and the identity-pilot sub-project.
- Spec Kit–driven, spec-first development process for the mobile product and the identity pilot.
- Foundational documentation: BRD, PRD, SRS, Architecture, Roadmap.
- Flutter app scaffold (`apps/mobile`) as the real product shell.

### 5.2 In scope (product, near-term)

- Camera-based discovery with family/species-level classification (reusing validated logic from the web alpha where applicable).
- GPS-aware encounters and familiarity (not biometric identity) as the default experience.
- A parallel, explicitly bounded **identity pilot** (cats/dogs only, via Petify) to test true individual recognition before it is a product feature.
- Squad collection, bonding/training, and turn-based PvE battles.
- Accounts, server-validated progress, and anti-duplicate-claim rules (via Supabase).

### 5.3 Out of scope (for now)

- Native AR overlays (ARKit/ARCore) — revisit after the core loop and identity pilot are validated.
- Real-time multiplayer or PvP.
- Species coverage beyond cats/dogs for true individual identity (birds/insects remain a research track, not a committed feature).
- Monetization model (explicitly deferred — see [PRD §9](PRD.md#9-monetization-deferred)).
- `twntis-film/` — unrelated project, entirely out of scope, not to be modified or referenced.

## 6. Success criteria

| Metric | Target | Source |
|---|---|---|
| Core loop completion (mobile) | A tester can go from cold install → first discovery → first battle without a guide | New, mobile-specific |
| Identity pilot — registered-animal recognition | Reported and compared against a 30-animal (15 cat / 15 dog) evaluation set before any go/no-go call | [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md) |
| Identity pilot — false "new animal" rate | Any wrong-animal award blocks expansion until understood | Same |
| Privacy | Zero raw images or precise coordinates persisted server-side without explicit, documented consent | New |
| Delivery | Spec Kit artifacts (constitution, spec, plan, tasks) exist and are current for both `apps/mobile` and `animon-identity-pilot` before implementation work begins | Process requirement |

## 7. Assumptions

- Flutter + Supabase is the team's chosen stack for the mobile product (decided 2026-11-05).
- The identity pilot proceeds as already planned in [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md), as a sub-project inside this monorepo rather than a fully separate repository.
- `animon-web` remains a read-only reference; any reusable game-design decisions (elements, families, battle math) are *ported*, not assumed to be final.
- No GPU training or hosting of third-party biometric models (e.g., MiewID) without confirming licensing terms.

## 8. Constraints

- Small team — avoid scope that requires a dedicated AR/engine specialist until the core loop and identity pilot are proven.
- Provider dependency risk: Petify pricing (~US$0.75/registered animal/month) must be revisited at scale before committing broadly.
- Legal/consent requirements for capturing images of animals (and incidentally, people/property) in public are unresolved and must be addressed before any public beta.

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Individual animal recognition doesn't work reliably outside controlled pet-registration contexts | Core differentiator fails | Identity pilot is explicitly scoped to de-risk this before product commitment |
| Privacy/consent exposure (photographing animals and bystanders in public) | Legal/reputational | Privacy requirements captured in SRS §6; no public beta without a reviewed consent/retention policy |
| Scope creep back toward the original heavy native AR/engine concept | Team can't ship | BRD §5.3 explicitly excludes AR/multiplayer from near-term scope |
| Duplicate/concurrent collection claims on the same real animal | Breaks trust in the collection model | Database-level exclusive-claim constraint, specified in SRS |

## 10. Open business questions

1. What is the monetization model (cosmetic, battle pass, energy, none at MVP)? — deferred, tracked in PRD.
2. What species beyond cats/dogs, if any, are commercially required for launch vs. acceptable as "collect by family only"?
3. What is the target launch market/region (affects privacy law — e.g., GDPR/BIPA-style biometric regulation relevant to "identity" framing)?
