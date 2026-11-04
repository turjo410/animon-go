# Software Requirements Specification (SRS) — Animon GO

| | |
|---|---|
| **Document owner** | Engineering |
| **Status** | Draft — foundational, for review |
| **Last updated** | 2026-11-05 |
| **Related** | [BRD](BRD.md) · [PRD](PRD.md) · [Architecture](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) |
| **Conformance note** | Structured loosely on IEEE 830. This is the pre-Spec-Kit foundation; once `/speckit-specify` and `/speckit-plan` run for a given feature, that feature's `specs/<feature>/spec.md` and `plan.md` become the authoritative, detailed source — this document stays as the stable cross-feature baseline and must not drift from it. |

## 1. Scope

Covers the mobile product (`apps/mobile`, Flutter/iOS/Android) and its backend (Supabase). The identity pilot (`animon-identity-pilot`) has its own Spec Kit instance and constitution, scoped separately per [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md); this SRS treats it as an external system accessed through a provider boundary (§4.4).

## 2. System overview

Animon GO is a client-server mobile application:

- **Client:** Flutter app (iOS + Android), owns capture UI, local game-state cache, and renders battles/roster/map.
- **Server:** Supabase (Postgres + Auth + Storage + Edge Functions), owns authoritative player progress, collection claims, and identity-provider calls that require a server-held credential.
- **Identity provider boundary:** an interface with a **mock** implementation (default, always available) and a **live** implementation (Petify, gated to the identity pilot) — see [Architecture §4](ARCHITECTURE.md).

## 3. Actors

| Actor | Description |
|---|---|
| Player | Authenticated mobile app user |
| Operator | Reviews uncertain identity-pilot matches and new-enrollment requests (identity pilot only) |
| System (scheduled) | Resets daily trail rewards, expires stale sessions |

## 4. Functional requirements

Each requirement is written to be acceptance-testable. IDs are stable; do not renumber — deprecate instead.

### 4.1 Discovery and classification

- **FR-101**: The app SHALL let a player submit a captured image (live camera preferred; photo fallback for development/testing) for family classification.
- **FR-102**: Classification SHALL return one of {Feline, Canine, Avian, Rodent, Insect} with a confidence score, or an explicit "no confident match" result.
- **FR-103**: A classification confidence below the configured per-family threshold SHALL NOT award a creature (soft fail), and SHALL be distinguishable to the player from a successful discovery.
- **FR-104**: No raw captured image SHALL be persisted beyond the duration needed to classify it, unless the player is in the explicitly-labeled identity pilot flow with disclosed retention.

### 4.2 Variant resolution ("awakening")

- **FR-110**: Given a classified family and a context attunement (day / rain / night), the system SHALL deterministically resolve one of 15 defined creature variants (5 families × 3 attunements → distinct elements per [PRD §6](PRD.md#6-game-design-reference-ported-from-the-web-alpha)).
- **FR-111**: The attunement source (simulated vs. real weather/time) SHALL be explicit in game state and never presented to the player as a real-world weather claim unless backed by a real weather feed (Phase 3+).

### 4.3 Familiarity (default collection model)

- **FR-120**: On a new discovery, the system SHALL classify the encounter as "New encounter", "Probably familiar", or "Returning presence" based on family match, elapsed time (≤ 7 days), and a family-specific GPS radius, per the ported web-alpha algorithm ([`animon-web/src/lib/game.ts`](../animon-web/src/lib/game.ts) `familiarity()`).
- **FR-121**: Familiarity SHALL NOT be presented or documented as biometric identity. Only the identity pilot (§4.4) may claim individual recognition, and only within its own labeled flow.
- **FR-122**: Location used for familiarity SHALL be opt-in and SHALL be stored rounded/approximate, never full-precision, consistent with the web alpha's three-decimal rounding precedent.

### 4.4 Identity pilot boundary (cats/dogs only)

- **FR-130**: The system SHALL expose an identity-provider interface with at least a `mock` and a `petify` implementation; the active implementation SHALL be explicit in all stored results (never ambiguous between mock and live evidence).
- **FR-131**: A confident, verified match to a previously-registered animal SHALL reuse that animal's existing shared record rather than creating a new one.
- **FR-132**: An uncertain, unfamiliar, or failed identity result SHALL award nothing automatically and MAY enter operator review.
- **FR-133**: Exactly one active collection claim SHALL be permitted per verified animal identity, enforced at the database level (not application-logic-only), to prevent concurrent-claim races.
- **FR-134**: All identity-provider results (mock and live) SHALL be server-verified before affecting collection state; a client-only or redirect-only result SHALL NOT be trusted.

Detailed acceptance criteria for FR-130…134 live in `animon-identity-pilot/specs/` once generated by that sub-project's Spec Kit workflow — see [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md) §5.

### 4.5 Collection, bonding, squad

- **FR-140**: The system SHALL maintain a player roster of owned companions, each with level, bond value, and discovery context.
- **FR-141**: Training a companion SHALL cost 30 essence per level and SHALL increase HP by 6 and Attack by 2 per level beyond the first (ported from the web alpha; revisit balance in `specs/` during Phase 1 planning).
- **FR-142**: The player SHALL maintain exactly 3 companions as an active squad at any time, selectable from the roster.

### 4.6 Battle (PvE trials)

- **FR-150**: The system SHALL support turn-based 3v3 battles between the player's squad and a rotating set of enemy companions, scaled by wave number.
- **FR-151**: Each companion SHALL support four actions: basic attack, elemental skill (cooldown), heal/Renewal (cooldown, capped restore), and guard (halves next incoming damage).
- **FR-152**: Damage SHALL apply the elemental advantage multiplier (+40%) per the defined advantage web (Fire↔Earth↔Water, Air→Earth, Light↔Dark).
- **FR-153**: Clearing a wave SHALL award a fixed essence + XP bundle exactly once per wave instance (no reward farming by replaying the same cleared instance).
- **FR-154**: A defeated squad (all companions at 0 HP) SHALL end the trial in a defeat state with no partial wave reward.

### 4.7 Accounts and persistence

- **FR-160**: The system SHALL require an authenticated account (Supabase Auth) to persist progress server-side; local/offline play MAY be supported but SHALL sync and reconcile against the server as source of truth once online.
- **FR-161**: All reward-affecting actions (training cost, wave clear reward, daily trail reward) SHALL be validated server-side; the client SHALL NOT be the sole authority for currency or XP changes.

### 4.8 Daily engagement

- **FR-170**: The system SHALL grant a daily trail reward once per local calendar date per player, server-validated against server time (not client-reported time) to prevent clock manipulation.

## 5. Non-functional requirements

| ID | Requirement | Status |
|---|---|---|
| NFR-ACC-1 | Family classification accuracy ≥ a measured, documented threshold per device tier and animal distance band. The originally stated 88% target is **carried over, not validated** — Phase 1 must measure and either confirm or replace it. | Open — must validate |
| NFR-LAT-1 | Classification latency target ≤ 1.5s on a defined reference device tier, measured and documented before claiming it. | Open — must validate |
| NFR-PRIV-1 | See §6 (Privacy & security). | Binding |
| NFR-REL-1 | Reward-affecting operations (training, wave clear, daily reward, identity claim) SHALL be idempotent against retries/duplicate callbacks. | Binding |
| NFR-AVAIL-1 | Core loop (discovery, collection, battle) SHALL be usable with degraded/offline connectivity for already-synced data; server-dependent actions SHALL fail visibly rather than silently. | Binding |
| NFR-PERF-1 | App cold start and battle-screen frame rate targets to be defined during Phase 1 planning against actual target devices (not yet benchmarked). | Open — must define |

## 6. Privacy & security requirements

- **SEC-1**: Camera images SHALL NOT be uploaded to any server except where a feature's spec explicitly discloses it (e.g., a live identity-provider capture flow) and the player has been informed before capture.
- **SEC-2**: Location data used for familiarity SHALL be opt-in, approximate (rounded), and never exposed publicly (e.g., no public map of exact encounter coordinates).
- **SEC-3**: No feature SHALL claim or imply biometric identification of an animal outside the identity pilot's explicitly labeled flow, and that flow SHALL itself disclose mock-vs-live status at all times.
- **SEC-4**: Provider credentials (e.g., Petify server keys) SHALL be held server-side only (Supabase Edge Functions / server environment), never embedded in the mobile client.
- **SEC-5**: Participant/evaluation data gathered for the identity pilot SHALL be excluded from version control and from any production analytics pipeline, per [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md) §2.
- **SEC-6**: Before any public beta, a reviewed consent and data-retention policy covering bystanders and pet owners captured incidentally SHALL exist (tracked as an open item — see [BRD §9](BRD.md#9-risks)).

## 7. Data requirements (high-level)

| Entity | Key attributes | Notes |
|---|---|---|
| `player` | id, auth identity, display name, created_at | Supabase Auth-backed |
| `companion_owned` | id, player_id, creature_id, level, bond, discovered_context | One row per owned companion instance |
| `creature_def` | id, name, family, element, rarity, base stats, skill, passive | Static/reference data, seeded from ported web-alpha definitions |
| `encounter` | id, player_id, family, timestamp, approx_location, is_demo | Drives familiarity; approx_location nullable if location declined |
| `squad` | player_id, companion_owned_id × 3 | Exactly 3 slots |
| `battle_session` | id, player_id, wave, state, log | Ephemeral/session-scoped |
| `animal_identity` (pilot only) | id, species_scope, provider, external_ref, claim_owner_player_id | One active claim enforced via unique constraint |

Full schema design is deferred to `plan.md`/`data-model.md` generated by Spec Kit for each feature, not hand-specified here.

## 8. Interfaces

- **Mobile ↔ Supabase**: REST/Realtime via the official Supabase Flutter client; Auth via Supabase Auth.
- **Server ↔ Identity provider**: server-to-server only (Edge Function ↔ Petify API), per [`docs/research/identity-pilot-setup-plan.md`](research/identity-pilot-setup-plan.md).
- **Mobile ↔ Device**: camera (capture), location (opt-in, approximate), local secure storage (session cache).

## 9. Constraints

- No custom ML model training is in scope until an existing classifier/provider is shown insufficient (carried over from [`docs/research/animal-identification-rnd.md`](research/animal-identification-rnd.md)).
- Flutter + Supabase is the fixed stack for Phase 1 (see [Architecture](ARCHITECTURE.md)); revisiting this requires an explicit decision record under `docs/decisions/`.

## 10. Traceability

Each `FR-xxx` SHOULD be traceable to a Spec Kit feature spec once planning begins. Maintain the mapping in `docs/decisions/` or a future `docs/traceability.md` rather than editing requirement IDs after the fact.
