# Product Requirements Document (PRD) — Animon GO

| | |
|---|---|
| **Document owner** | Product |
| **Status** | Draft — foundational, for review |
| **Last updated** | 2026-11-05 |
| **Related** | [BRD](BRD.md) · [SRS](SRS.md) · [Architecture](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) |

## 1. Product vision

Walk outside, find a real animal, and watch it awaken into an Animon — a collectible elemental creature tied to that discovery. Build a squad, bond with your companions, and test them in trials. Animon GO is a location-based mobile game (iOS + Android, Flutter) in the spirit of Pokémon GO, distinguished by discovery coming from *real animals encountered in the world* rather than fixed virtual spawns.

## 2. Target platform

- **Primary:** native mobile, iOS + Android, built with Flutter (`apps/mobile`).
- **Not the product:** `animon-web` is a browser reference prototype used to validate game design and mechanics; it is not shipped to players.

## 3. Personas

| Persona | Description | Needs |
|---|---|---|
| **The Explorer** | Walks dogs, visits parks, casually curious | Low-friction capture, satisfying "awaken" moment, doesn't need to understand the tech |
| **The Collector** | Wants to complete the roster, cares about rarity and variants | Clear collection UI, journal/history, meaningful bonding progression |
| **The Competitor** | Wants strong squads, optimizes elemental matchups | Transparent stats, type-advantage clarity, challenging PvE trials |
| **The Pet Owner (identity pilot)** | Has a registered pet that other players might also encounter | Trusts that their pet isn't being tracked/identified without consent; sees their pet correctly recognized as already-collected rather than re-claimed |

## 4. Core loop

```
Discover → Classify → Awaken → Collect → Bond/Train → Squad → Battle (PvE trial) → Reward → Repeat
```

1. **Discover** — player points the camera at a real animal (or, during early development/testing, a photo).
2. **Classify** — on-device/edge classification determines the animal **family** (Feline, Canine, Avian, Rodent, Insect) with a confidence gate; low-confidence results soft-fail (no award) rather than guessing.
3. **Awaken** — the family, combined with a contextual attunement (day / rain / night, derived from local time/weather later), resolves to one of 15 elemental creature variants (5 families × 3 attunements).
4. **Collect** — the creature is added to the player's roster if it's new, or reinforces **familiarity** if it's a plausible repeat encounter (same family, within a family-specific GPS radius, within 7 days) — explicitly *familiarity*, never biometric identity, for the default product.
5. **Bond/Train** — spend **essence** (currency) to level a companion; leveling increases HP and Attack.
6. **Squad** — maintain exactly 3 active companions.
7. **Battle** — turn-based 3v3 PvE trials against rotating, wave-scaled opponents, using basic attack / elemental skill (cooldown) / heal (Renewal, cooldown) / guard (ward).
8. **Reward** — clearing a wave awards essence and explorer XP once per wave instance; daily trail rewards encourage return visits.

## 5. Feature set

### 5.1 MVP (Phase 1 — mobile core loop)

- Camera capture → family classification (port/upgrade of the web alpha's approach; evaluate a purpose-built on-device model vs. a generic classifier — see SRS NFR-ACC).
- GPS-based familiarity (opt-in, approximate/rounded location, no public exposure of coordinates).
- Attunement-based variant resolution (day/rain/night) producing all 15 creatures across 5 families × 6 elements.
- Roster, companion detail, training/bonding, 3-member squad management.
- Turn-based PvE trial battles: basic attack, elemental skill, heal, guard; elemental advantage web (Fire↔Earth↔Water, Air→Earth, Light↔Dark at +40% damage).
- Field journal and encounter history (bounded, exportable).
- Accounts + server-persisted progress (Supabase Auth + Postgres), replacing the web alpha's browser-only local storage.
- Daily trail rewards.

### 5.2 Phase 2 — identity pilot integration

- Ship the **identity pilot** (`animon-identity-pilot`, see [BRD §6](BRD.md#6-success-criteria) and [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md)) as a bounded, clearly-labeled experiment: cats/dogs only, via Petify, mock mode first.
- If validated: integrate true individual recognition as an *additional, opt-in* layer on top of family-level discovery — a confidently-recognized registered animal reuses its existing record; an uncertain result never silently creates a new one.
- If not validated: ship without it, keep family-level familiarity as the permanent default, and record the decision.

### 5.3 Phase 3 — world features (not committed)

- Map view of nearby activity (no AR commitment yet).
- ARKit/ARCore overlay for the "awakening" moment.
- Expanded species coverage, contingent on identity research (birds/insects remain research-only per [`docs/research/animal-identification-rnd.md`](research/animal-identification-rnd.md)).
- Social/competitive features (trading, leaderboards, multiplayer battles).

## 6. Game design reference (ported from the web alpha)

The web alpha (`animon-web`) validated the following design, which Phase 1 should port and adapt for mobile rather than redesign from scratch:

- **Families:** Feline, Canine, Avian, Rodent, Insect.
- **Elements:** Earth, Fire, Water, Air, Light, Dark.
- **Advantage web:** Fire→Earth, Earth→Water, Water→Fire, Air→Earth, Light↔Dark deal +40% damage.
- **Creature stats:** HP, Attack, Defense, Speed, one cooldown skill, one passive trait, rarity (Common/Uncommon/Rare).
- **Battle math:** `damage = max(4, round((attacker.attack * power - defender.defense * 0.3) * advantageMultiplier * guardMultiplier))`.
- **Progression:** training costs 30 essence; each level beyond the first adds +6 HP and +2 Attack; a cleared wave awards 60 essence + 100 XP once per wave instance.
- **Familiarity tiers:** "New encounter" / "Probably familiar" / "Returning presence", derived from family-specific radii and 7-day recency — not identity.

Full source: [`animon-web/src/lib/data.ts`](../animon-web/src/lib/data.ts), [`animon-web/src/lib/game.ts`](../animon-web/src/lib/game.ts), [`animon-web/docs/IMPLEMENTATION.md`](../animon-web/docs/IMPLEMENTATION.md).

## 7. Non-functional targets (carried over, unvalidated)

The original concept targeted **88% family-classification accuracy** and **1.5-second** classification latency. The web alpha explicitly did **not** validate these on real devices. Phase 1 must either validate these targets per-device/per-distance, or adopt revised, measured targets — see [SRS §5](SRS.md#5-non-functional-requirements).

## 8. Privacy and safety requirements (summary)

See [SRS §6](SRS.md#6-privacy-security-requirements) for the full specification. Summary: no raw captured images leave the device/provider boundary without explicit purpose; location is opt-in and approximate by default; no biometric identity claims outside the explicitly-labeled identity pilot; bystander and pet-owner consent must be addressed before any public beta.

## 9. Monetization (deferred)

No monetization model is committed. Candidates to evaluate post-MVP: cosmetic customization, a seasonal battle pass, or energy/stamina systems — none of which should gate the core discovery loop. This section exists so monetization isn't silently assumed; it is an open business question (see [BRD §10](BRD.md#10-open-business-questions)).

## 10. Out of scope

See [BRD §5.3](BRD.md#53-out-of-scope-for-now). In particular: real-time multiplayer/PvP, AR overlays, and any species identity claims beyond the bounded cats/dogs pilot are explicitly not part of the MVP.
