# Feature Specification: Mobile Core Loop

**Feature Branch**: `001-mobile-core-loop`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Build the Animon GO mobile MVP core loop. A player opens the app, grants camera and (optionally) location permission, and points the camera at a real animal. The app classifies the animal into one of five families (Feline, Canine, Avian, Rodent, Insect); a low-confidence result fails softly and awards nothing. A confident classification, combined with a context attunement (day, rain, or night), resolves to one of fifteen elemental creature variants, which is added to the player's roster if new, or reinforces familiarity (New encounter / Probably familiar / Returning presence) if a plausible repeat based on family, 7-day recency, and a family-specific GPS radius — never framed as biometric identity. The player maintains a roster of owned companions, trains them by spending an 'essence' currency to level them up (each level adds HP and Attack), and keeps exactly three companions as an active squad. The player can enter a turn-based PvE trial: 3-versus-3 battles against a rotating, wave-scaled set of enemies, where each companion can perform a basic attack, an elemental skill (on cooldown), a heal (on cooldown, capped), or a guard action that halves incoming damage, and elemental advantages (Fire/Earth/Water triangle, Air beats Earth, Light and Dark beat each other) deal 40% bonus damage. Clearing a wave awards a fixed essence and XP bundle exactly once per wave instance. The player can also claim a daily trail reward once per local calendar day. All progress (roster, squad, currency, XP, claimed rewards) is tied to an authenticated account and persisted server-side as the source of truth, with reward-affecting actions validated server-side rather than trusted from the client. A field journal records discoveries and notable events, bounded in size. This feature targets the native mobile app (iOS and Android); it explicitly excludes AR overlays, real-time multiplayer, monetization, and true individual-animal identification (which is a separate, bounded pilot)."

**Traceability**: Baseline — [`docs/BRD.md`](../../docs/BRD.md), [`docs/PRD.md`](../../docs/PRD.md) §5.1, [`docs/SRS.md`](../../docs/SRS.md) FR-101…FR-170, [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md). Game design ported from [`animon-web`](../../animon-web) (reference prototype only).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and collect a companion (Priority: P1)

A player opens the app for the first time, grants camera access, and points their phone's camera at a real animal (e.g., a neighborhood cat). The app recognizes the animal's family and, moments later, shows an "awakening" reveal: the animal has resolved into an elemental creature companion, now added to the player's roster.

**Why this priority**: This is the entire premise of the product — the moment that has to work, and work in a way that feels good, before anything else matters. Without it, there is no game.

**Independent Test**: Can be fully tested by pointing the camera at a real or photographed animal and confirming a new companion appears in the roster with correct family/element/rarity, or that a clear "no confident match" result appears for an ambiguous image — delivers the core discovery value on its own, with no battle or training system required.

**Acceptance Scenarios**:

1. **Given** a player with camera permission granted, **When** they capture a clear image of a cat, **Then** the app shows a confident Feline classification and awards one of the three Feline elemental variants (day/rain/night) to their roster.
2. **Given** a player capturing an ambiguous or unrecognizable image, **When** classification confidence falls below the configured threshold, **Then** the app shows a clear "no confident match" result and awards nothing.
3. **Given** a player who has previously discovered a Feline companion within the last 7 days and within the Feline familiarity radius of their current location, **When** they discover another Feline, **Then** the encounter is tagged "Probably familiar" or "Returning presence" rather than presented as a brand-new identity.
4. **Given** a player who has declined location permission, **When** they make a discovery, **Then** family-level discovery still works normally, and familiarity falls back to non-location signals (family + recency) only.

---

### User Story 2 - Train a squad and win a trial (Priority: P2)

A player with at least one owned companion spends essence to train it, assembles an active squad of exactly three companions, and enters a turn-based PvE trial against a wave of enemy creatures, using basic attacks, elemental skills, heals, and guards to win.

**Why this priority**: This is what gives discovery ongoing purpose — without training and battling, collecting companions has no further payoff loop. It depends on User Story 1 providing at least one owned companion.

**Independent Test**: Can be fully tested by granting a test account three pre-owned companions, assembling a squad, and playing a trial to victory or defeat — delivers the progression/combat value independently of how companions were originally discovered.

**Acceptance Scenarios**:

1. **Given** a player with enough essence, **When** they train an owned companion, **Then** its level increases by one and its HP and Attack increase by the defined per-level amounts, and the essence cost is deducted exactly once.
2. **Given** a player with three or more owned companions, **When** they set their active squad, **Then** exactly three companions are marked active and all others are benched.
3. **Given** a player in an active trial, **When** they select an elemental skill on cooldown, **Then** the action is rejected and no turn is consumed.
4. **Given** an attacking companion whose element is advantaged against the defender's element, **When** it attacks, **Then** the damage dealt is 40% higher than the non-advantaged baseline.
5. **Given** a player who defeats all enemies in a wave for the first time, **When** the wave ends, **Then** they receive the fixed essence and XP reward exactly once; replaying the same cleared wave instance does not grant it again.
6. **Given** a player whose entire squad reaches 0 HP, **When** the last companion falls, **Then** the trial ends in a defeat state with no wave reward.

---

### User Story 3 - Keep coming back (Priority: P3)

A returning player opens the app, claims a daily trail reward if not already claimed today, and reviews their field journal of past discoveries and notable events.

**Why this priority**: Supports retention once the core loop (P1) and progression loop (P2) already work; it is additive engagement, not required for the game to be playable or demonstrable.

**Independent Test**: Can be fully tested by advancing a test account's server-recorded date and confirming the daily reward becomes claimable again, and that journal entries persist and remain bounded — delivers retention value independently of discovery or battle outcomes on that day.

**Acceptance Scenarios**:

1. **Given** a player who has not claimed a trail reward on the current local calendar date, **When** they claim it, **Then** they receive the reward exactly once and cannot claim it again until the next local calendar date, as determined by server time.
2. **Given** a player who discovers a new companion or completes a notable event, **When** the event occurs, **Then** a journal entry is recorded and remains available until the bounded history limit is exceeded, at which point the oldest entries are dropped first.

---

### Edge Cases

- What happens when the device has no network connectivity at the moment of a reward-affecting action (training, wave clear, daily claim)? The action must fail visibly and be retryable once connectivity returns, rather than silently granting a reward the server never validated.
- How does the system handle a player with fewer than three owned companions attempting to enter a trial? Entry is blocked with a clear explanation, since exactly three active squad members are required.
- How does the system handle two reward-affecting requests arriving out of order or duplicated (e.g., a retried network call double-submitting a wave-clear reward)? The server must treat the operation as idempotent and grant the reward only once per wave instance.
- What happens when a player's local clock disagrees with server time for the daily trail reward? The daily boundary is determined by server time, not client-reported time.
- What happens when location permission is granted but GPS signal is unavailable at the moment of discovery? The discovery still proceeds using family + recency-only familiarity, consistent with location being opt-in and best-effort.
- What happens when a player captures an image containing more than one animal, or an animal plus a person? Classification proceeds on a best-effort basis against the dominant/clearest subject; this spec does not require multi-subject detection or separation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST let a player capture an image via the device camera for family classification. *(SRS FR-101)*
- **FR-002**: The system MUST classify a captured image into one of {Feline, Canine, Avian, Rodent, Insect} with an associated confidence score, or return an explicit no-confident-match result. *(SRS FR-102)*
- **FR-003**: The system MUST NOT award a companion when classification confidence is below the configured per-family threshold, and MUST present this outcome as distinct from a successful discovery. *(SRS FR-103)*
- **FR-004**: The system MUST NOT persist a raw captured image beyond what is needed to perform classification. *(SRS FR-104)*
- **FR-005**: Given a classified family and a context attunement (day, rain, or night), the system MUST deterministically resolve exactly one of fifteen defined creature variants (5 families × 3 attunements). *(SRS FR-110)*
- **FR-006**: The system MUST represent the attunement source (simulated vs. a real weather/time feed) explicitly in game state and MUST NOT present a simulated attunement as a real-world weather observation. *(SRS FR-111)*
- **FR-007**: On each discovery, the system MUST classify the encounter as "New encounter," "Probably familiar," or "Returning presence" based on family match, elapsed time (≤ 7 days), and a family-specific GPS radius. *(SRS FR-120)*
- **FR-008**: The system MUST NOT present familiarity as, or imply, biometric identification of an individual animal. *(SRS FR-121)*
- **FR-009**: Location used for familiarity MUST be opt-in and MUST be stored only in approximate/rounded form. *(SRS FR-122)*
- **FR-010**: The system MUST maintain a player roster of owned companions, each with a level, a bond value, and the context of its discovery. *(SRS FR-140)*
- **FR-011**: The system MUST let a player spend essence to train an owned companion, increasing its level by one per training action, with HP and Attack increasing by fixed amounts per level beyond the first. *(SRS FR-141)*
- **FR-012**: The system MUST require the player to maintain exactly three owned companions as the active squad at any time. *(SRS FR-142)*
- **FR-013**: The system MUST support turn-based 3-vs-3 battles between the player's squad and a rotating, wave-scaled set of enemy companions. *(SRS FR-150)*
- **FR-014**: Each companion in battle MUST support four actions: basic attack, elemental skill (cooldown-gated), heal (cooldown-gated, capped restore amount), and guard (halves next incoming damage). *(SRS FR-151)*
- **FR-015**: Battle damage calculations MUST apply a 40% bonus when the attacker's element is advantaged against the defender's element, per the defined advantage relationships (Fire↔Earth↔Water triangle, Air beats Earth, Light and Dark beat each other). *(SRS FR-152)*
- **FR-016**: Clearing a wave MUST award a fixed essence-and-XP bundle exactly once per wave instance; replaying an already-cleared wave instance MUST NOT grant the reward again. *(SRS FR-153)*
- **FR-017**: A battle in which the player's entire squad reaches 0 HP MUST end in a defeat state with no wave reward granted. *(SRS FR-154)*
- **FR-018**: The system MUST require an authenticated account to persist progress server-side, and MUST treat server-stored state as the source of truth when reconciling with any local/offline state. *(SRS FR-160)*
- **FR-019**: All reward-affecting actions (training cost, wave-clear reward, daily trail reward) MUST be validated and applied server-side; the client MUST NOT be able to independently grant currency or XP. *(SRS FR-161)*
- **FR-020**: The system MUST grant a daily trail reward at most once per local calendar date per player, with the date boundary determined by server time. *(SRS FR-170)*
- **FR-021**: The system MUST maintain a field journal of discoveries and notable events per player, bounded to a fixed maximum number of entries, discarding the oldest entries first once the bound is exceeded.

### Key Entities

- **Player**: An authenticated account; owns a roster, a squad, currency and XP balances, journal entries, and claimed-reward history.
- **Owned Companion**: An instance of a creature definition held by a specific player, with its own level, bond value, and discovery context; distinct from the shared, static creature definition it is based on.
- **Creature Definition**: The static definition of one of the fifteen elemental variants — family, element, rarity, base stats, skill, and passive trait — shared across all players.
- **Encounter**: A record of one discovery event: family, timestamp, approximate location (if granted), and whether it was a real or simulated/demo capture; used to compute familiarity.
- **Squad**: The player's current selection of exactly three owned companions marked active for battle.
- **Battle Session**: The in-progress or completed state of one PvE trial: wave number, participant HP/cooldowns, turn order, and outcome.
- **Journal Entry**: A bounded, player-visible record of a discovery or notable event, with a title, detail, timestamp, and associated element.
- **Daily Reward Claim**: A record of whether the player has claimed their trail reward for the current (server-determined) local calendar date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time player can go from opening the app to having a new companion in their roster in under 2 minutes, without external instructions.
- **SC-002**: A player can assemble a 3-member squad and enter their first trial in under 1 minute from having at least three owned companions, without external instructions.
- **SC-003**: 100% of discoveries with confidence below the configured threshold result in no companion awarded and a result the player can distinguish from a successful discovery, across a defined internal test set of ambiguous/low-quality images.
- **SC-004**: 100% of simulated duplicate or out-of-order reward-affecting requests (training, wave-clear, daily claim) in automated testing result in the reward being granted at most once.
- **SC-005**: 100% of familiarity classifications in a defined set of scripted encounter sequences (varying family, elapsed time, and distance) match the expected "New encounter" / "Probably familiar" / "Returning presence" outcome.
- **SC-006**: Zero instances, across automated testing, of a player accessing a trial with a squad of fewer than three owned companions.

## Assumptions

- Classification accuracy and latency are **not** asserted by this spec. The originally-stated 88%/1.5s targets are unvalidated (per `docs/PRD.md` §7) and must be measured during planning/implementation on real target devices, not assumed here.
- Context attunement (day/rain/night) is simulated for this feature, consistent with the validated web-alpha design; integrating a real weather feed is explicitly out of scope here and tracked as a later roadmap phase (`docs/ROADMAP.md` Phase 4).
- New players are granted a fixed starter set of owned companions at onboarding (ported from the web alpha's three-starter pattern), so User Story 2 is testable without first requiring three successful live discoveries. The exact starter set is a planning-level decision, not fixed by this spec.
- "Photo fallback" capture (vs. only a live camera feed) is assumed available for development/testing and lower-end scenarios, consistent with `docs/SRS.md` FR-101.
- True individual-animal identification is explicitly out of scope for this feature; it is governed separately by the identity pilot (`animon-identity-pilot/`) and is not a dependency of this spec.
- Offline play is assumed to support viewing already-synced state, but any new reward-affecting action requires connectivity to the server to be authoritative, per `docs/SRS.md` NFR-AVAIL-1.
