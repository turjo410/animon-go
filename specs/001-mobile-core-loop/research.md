# Research — Mobile Core Loop (Phase 0)

**Feature**: `specs/001-mobile-core-loop` | **Date**: 2026-11-09 | **Plan**: [plan.md](plan.md)

Each entry records a decision, why it was chosen, and the alternatives considered. Game constants are ported from the reference prototype ([`animon-web/src/lib/data.ts`](../../animon-web/src/lib/data.ts), [`game.ts`](../../animon-web/src/lib/game.ts), [`App.tsx`](../../animon-web/src/App.tsx)). The prototype was read only, never edited.

---

## R1 — Flutter toolchain and package versions

- **Decision**: Build on the installed **Flutter 3.35.4 / Dart 3.9.2** (FVM default) and pin the newest package versions that resolve on it:

  | Package | Version | Purpose |
  |---|---|---|
  | `flutter_riverpod` | 3.3.2 | State management |
  | `go_router` | 17.2.3 | Navigation |
  | `supabase_flutter` | 2.18.3 | Backend client |
  | `camera` | 0.12.0+1 | Live camera capture |
  | `image_picker` | 1.2.2 | Photo fallback |
  | `geolocator` | 14.0.2 | Opt-in location |
  | `shared_preferences` | 2.5.5 | Offline snapshot cache |
  | `uuid` | 4.6.0 | Request IDs |
  | `mocktail` | 1.0.5 | Dev: test mocks |

- **Rationale**: `flutter pub add --dry-run` confirmed these resolve on Dart 3.9.2. The latest releases (Riverpod 3.5, go_router 18, camera 0.12.2) require Dart ≥ 3.12, which would force a Flutter upgrade in the same change as the feature.
- **Alternatives**: Upgrade Flutter first. Deferred to a separate chore so a toolchain bump isn't mixed with feature work.

## R2 — State management

- **Decision**: **Riverpod 3**, using plain `Notifier`/`AsyncNotifier` providers **without code generation**.
- **Rationale**: Riverpod is testable without widgets (`ProviderContainer`), and repositories can be overridden in tests and in local dev mode. Skipping codegen keeps the build simple: there are no `build_runner` steps.
- **Alternatives**: Bloc (more boilerplate for this size); Provider (weaker testing and override story); riverpod_generator (an extra build step with no current need).

## R3 — Where the game rules live

- **Decision**: All rules are **pure Dart with no Flutter imports**, in `apps/mobile/lib/core/game/`:
  - variant resolution
  - familiarity
  - damage and battle turns
  - training and stats
  - rewards
  - journal bounding

  Domain types live in `lib/data/models/`. The rules take explicit inputs, including the current time, and return new immutable values.
- **Rationale**: ARCHITECTURE §3 asks for "pure, testable game rules … plain Dart functions mirroring game.ts". Purity is what makes the server-side replay in R4 and the parity checks in R5 possible.
- **Alternatives**: Rules inside widgets or notifiers. Rejected: they couldn't be tested or replayed.

## R4 — Server authority over battle rewards

- **Decision**: **Deterministic replay.**
  1. The client calls `start_trial`. The server creates a `battle_session` holding a snapshot of the squad (creature IDs and levels) and the wave number.
  2. The client plays the battle locally with the deterministic engine and records the ordered list of actions.
  3. When the battle ends, the client sends `{session_id, actions[]}` to the `complete-trial` Edge Function.
  4. The function replays the actions with the TypeScript port of the same engine, using the server's snapshot rather than any stats from the client. It grants the wave reward only if the replay ends in `victory`, and only once per session.
- **Rationale**: This satisfies FR-016/FR-017/FR-019 and constitution IV without a network round-trip on every turn. The prototype engine is already fully deterministic: enemies respond by turn index, and nothing is random.
- **Alternatives**:
  - (a) A server round-trip per turn: latency on every tap, and the battle breaks on a weak connection.
  - (b) Trust a client "I won" flag: violates constitution IV.
  - (c) Run Dart on the server: Supabase Edge Functions are Deno/TypeScript.

## R5 — Keeping the Dart and TypeScript rules identical

- **Decision**: A shared folder of **golden test vectors**, `shared/game-vectors/*.json` at the repo root. Each vector holds inputs and expected outputs for `damage`, `battleTurn` sequences, `familiarity`, `chooseVariant` and `trainCost`. The Dart tests (`flutter test`) and the Deno tests (`deno test`) both load the same files, and a rule change must update the vectors. Vectors are seeded from cases in the prototype's `game.test.ts`.
- **Rationale**: This is the cheapest reliable way to stop two implementations drifting apart. Any divergence fails CI on whichever side is wrong.
- **Alternatives**: Generate one from the other (no mature Dart→TS path); a single WASM engine (excessive for this rule set).

## R6 — Server write path and idempotency

- **Decision**: Clients never write tables directly. Row Level Security lets a player **read** only their own rows; all writes go through:

  | Operation | Mechanism | Why |
  |---|---|---|
  | `bootstrap_player`, `train_companion`, `set_squad`, `start_trial`, `claim_trail` | Postgres RPC (`security definer`, one transaction) | Simple arithmetic and constraint checks |
  | `discover`, `complete-trial` | Edge Function (TypeScript) | Needs the game rules (R4/R5) |

  Every reward-affecting call carries a client-generated `request_id` (UUID v4) that stays the same across retries. A `reward_ledger` table with `unique (player_id, kind, instance_key)` is the single source of "granted at most once". Repeating a call returns the original result without granting again.
- **Rationale**: This covers NFR-REL-1, FR-019, SC-004 and the duplicate/out-of-order edge cases. A unique constraint holds even when two identical requests race.
- **Alternatives**: Check-then-write in application code (race-prone); Edge Functions for everything (needless cold starts for simple arithmetic).

## R7 — Daily boundary "by server time, in local calendar date"

- **Decision**:
  - Store the player's IANA `timezone` on their profile. It is captured from the device at bootstrap.
  - The server computes `trail_date = (now() at time zone players.timezone)::date`. The client clock is never consulted.
  - A timezone change is accepted at most **once per 24 h**, so a player can't farm extra days by hopping timezones.
- **Rationale**: This satisfies FR-020 and the clock-disagreement edge case. "Local calendar date" needs a timezone, and "server time" needs `now()` on the server.
- **Alternatives**: UTC dates (the day would reset mid-afternoon for some players); the client's reported date (spoofable).

## R8 — Familiarity when location is missing (spec vs. prototype conflict)

- **Finding**: The prototype's `familiarity()` returns **"New encounter"** whenever either encounter has no coordinates. Spec US1 scenario 4 says familiarity "falls back to non-location signals (family + recency) only".
- **Decision**: **The spec wins.** If either encounter lacks coordinates, a same-family encounter within 7 days still counts as a match. The result is **capped at "Probably familiar"** and never reaches "Returning presence", because the evidence is weaker without location. When both have coordinates, the prototype's rule applies unchanged, with these family radii:

  | Family | Radius |
  |---|---|
  | Feline | 200 m |
  | Canine | 300 m |
  | Avian | 120 m |
  | Rodent | 80 m |
  | Insect | 60 m |

  Demo and simulated encounters only ever match other demo encounters.

  **Precise rule** (this is what the Dart and TS engines and `shared/game-vectors/familiarity.json` implement):

  1. **Candidates.** For each prior encounter of the same family with `0 ≤ Δt < 7 days`:
     - **Demo**: if both are demo, it's a *strong* match. If exactly one is demo, it's no match.
     - **Real, both located**: a *strong* match if the distance is below the family radius. The distance uses the prototype's formula: `hypot(Δlat·111000, Δlon·111000·cos(lat))`.
     - **Real, either unlocated**: a *weak* match.
  2. **Result**:

     | Matches | Tag |
     |---|---|
     | No strong and no weak matches | New encounter |
     | Strong matches > 1 | Returning presence |
     | Otherwise (at least one match) | Probably familiar |
- **Rationale**: This follows the spec and SRS FR-120, and keeps FR-008: the wording never implies it's the same individual.
- **Follow-up**: The cap is a planning choice inside the spec's latitude. It will be noted in `docs/decisions/` when it is implemented, so `docs/PRD.md` §6 (the ported algorithm) doesn't silently drift.

## R9 — Location precision

- **Decision**: Round coordinates to **3 decimal places** (~110 m of latitude) on the device, before they leave it or are stored. This follows the prototype precedent cited in SRS FR-122. Location is opt-in through `geolocator`, and if permission is denied or there is no fix, discovery continues without it (R8).
- **Known consequence**: Rounding to ~110 m makes the 60–120 m radii (Insect, Rodent, Avian) coarse: two points rounded to the same cell are 0 m apart. That is acceptable for a heuristic that is explicitly not identity. It will be revisited with field data.
- **Alternatives**: Full precision (violates FR-122); geohash-6 (~1.2 km × 0.6 km, too coarse for every radius).

## R10 — Attunement (day / rain / night)

- **Decision**: Attunement is **simulated** in MVP. The scanner defaults it from the device's local hour (06:00–17:59 is day, otherwise night). "Rain" is a toggle the player picks, as in the prototype. Every encounter stores `attunement_source = 'simulated'`, and the UI labels it ("Simulated attunement"). The server accepts only `'simulated'` in this feature.
- **Rationale**: This satisfies FR-006/FR-111. A real weather feed is Roadmap Phase 4.
- **Alternatives**: A weather API now (out of scope, and a privacy and location question).

## R11 — Family classification seam (the model isn't chosen here)

- **Decision**: The `FamilyClassifier` interface ([contract](contracts/family-classifier.md)) has one implementation in this feature: **`MockFamilyClassifier`**. It is deterministic. In debug builds it shows a scripted picker (family and confidence); in tests it returns a fixed script.
  - Per-family confidence thresholds live in `ClassifierThresholds`, defaulting to **0.55** for every family (the prototype's value), and can be overridden in config.
  - The real model is ML Kit or the zero-shot SigLIP 2 image tower. It plugs into this seam after [`docs/research/model-evaluation-plan.md`](../../docs/research/model-evaluation-plan.md) step 6. Choosing it is **not** part of this plan.
- **Trust boundary**: The server can't verify what the camera saw, because images are never uploaded (FR-004). It therefore:
  - accepts only results at or above the threshold, with a valid family
  - rate-limits `discover` to **30 per hour**
  - caps discovery rewards at **20 rewarded discoveries per local day**

  This limits what a spoofed client could gain. The residual risk is accepted and documented.
- **Alternatives**: Upload images for server-side classification. Rejected: it conflicts with FR-004 and constitution VI.

## R12 — Captured images

- **Decision**: Frames and photos are held in memory or a temp file only long enough to classify. The temp file is deleted in a `finally` block straight after classification. Images are never uploaded, cached or written to the gallery (FR-004).

## R13 — Offline behaviour

- **Decision**:
  - The last server snapshot (roster, squad, balances, journal) is cached as JSON in `shared_preferences` and shown read-only when offline, with a visible "offline" banner.
  - Reward-affecting actions need the network. They fail visibly and offer **Retry**, which reuses the same `request_id` (R6).
  - Battles can be *played* offline, but a win is only rewarded once `complete-trial` succeeds. Pending completions are queued and retried with their original `session_id`.
- **Rationale**: This matches NFR-AVAIL-1 and the "no connectivity" edge case.

## R14 — Local development mode

- **Decision**: One `GameRepository` interface with two implementations:
  - `SupabaseGameRepository` (production)
  - `LocalGameRepository`: in memory, runs the same Dart rules to emulate the server, including the idempotency ledger

  The choice is made by `--dart-define=BACKEND=local|supabase`, defaulting to `local` in debug. Local mode is labelled in the UI ("Local dev mode — progress not saved to server").
- **Rationale**: The whole loop is playable and testable before the Supabase project exists, and widget tests run without a network.

## R15 — Authentication

- **Decision**: **Supabase anonymous sign-in** at first launch creates a real authenticated user (`auth.users`, `is_anonymous = true`). An email or Apple/Google identity can be linked later. `bootstrap_player` runs once per user and is idempotent.
- **Rationale**: This satisfies FR-018 ("an authenticated account") without a sign-up wall, keeping SC-001 (a new companion within 2 minutes) achievable.
- **Alternatives**: Mandatory email sign-up first (friction before the core moment).

## R16 — Starter set and economy (ported)

All values are from the prototype `App.tsx` and `data.ts`. They live in `lib/core/constants/` and in the shared vectors.

| Item | Value |
|---|---|
| Starter companions | Mosslyn L5 (bond 36), Cindertail L4 (bond 24), Dewfin L3 (bond 18); squad = all three |
| Starting balances | 240 essence, 120 XP |
| Discovery, new creature | Joins at level 1, bond 15; +50 XP, +15 essence |
| Discovery, already owned | +1 level, bond +15 (cap 100); +50 XP, +15 essence |
| Training | 30 essence → +1 level, bond +5 (cap 100) |
| Per-level stats | +6 HP and +2 Attack for each level above 1 |
| Wave clear | +60 essence, +100 XP |
| Player level | `floor(xp / 250) + 1` |
| Journal | Newest first; keeps 100 entries, dropping the oldest |
| Encounter history | 200 most recent kept |

## R17 — Daily trail rewards

- **Decision**: Port the prototype's three daily trails. Each can be claimed **once per server-determined local date**, and only once its goal is met. The server checks the goal from its own records for that date.

  | Trail | Goal | Reward |
  |---|---|---|
  | `scan` | 1 discovery today | 30 essence |
  | `bond` | 1 discovery of a family that has an earlier same-family encounter (a repeat) | 40 essence |
  | `trial` | 1 wave cleared today | 60 essence |

- **Rationale**: FR-020 says "a daily trail reward at most once per date". Applying the rule per trail keeps the validated prototype design. The ledger key is `trail:<trail_id>:<date>`.
- **Alternatives**: A single trail. Simpler, but throws away validated engagement design.

## R18 — Enemy rotation and wave scaling

- **Decision**: Wave *n* uses trio `ROTATION[(n − 1) mod 5]`. The rotation starts with the prototype's wave-1 trio and covers all 15 creatures:

  | Trio index | Enemies |
  |---|---|
  | 0 | acornix, breezlet, petalume |
  | 1 | sparkit, dewfin, mistmoth |
  | 2 | zephruff, brookhound, mosslyn |
  | 3 | duskwing, moonchest, cindertail |
  | 4 | nightpurr, solcat, lumoth |

  Scaling follows the prototype: enemy HP = base + (n − 1)·12 + slot·3; enemy damage power = 1 + (n − 1)·0.12.
- **Rationale**: This satisfies FR-013's "rotating, wave-scaled set". The prototype always used one trio.

## R19 — Battle mechanics (ported exactly)

- **Damage**: `max(4, round((atk·power − def·0.3) · (adv ? 1.4 : 1) · (guard ? 0.5 : 1)))`
- **Element advantage**: Fire > Earth > Water > Fire, Air > Earth, Light ⇄ Dark.
- **Skill**: power 1.65, cooldown 2. **Heal**: +36, capped at max HP, cooldown 3.
- **Guard**: halves the next enemy response.
- **Cooldowns**: every ally's cooldowns tick down at the start of each accepted action.
- **Rejected actions**: an action on cooldown returns the same state and consumes no turn.
- **After each player action**, the living enemy at index `(turn − 1) mod living` responds against the active ally.
- **When a unit falls**, the active ally advances to the next living ally, and the target advances to the next living enemy.

## R20 — Testing strategy

| Layer | Tooling | What |
|---|---|---|
| Domain rules (Dart) | `flutter test` (pure Dart) | Every FR-005/007/011/014/015/016/017/021 rule, plus the golden vectors (R5) |
| Notifiers / repositories | `flutter test` + `mocktail`, `ProviderContainer` | Idempotent retry, offline failure, local-mode ledger |
| Widgets | `flutter test` widget tests | Discovery result (success vs. soft fail distinguishable), squad screen (exactly 3), battle actions (cooldown rejection) |
| Database | `supabase test db` (pgTAP) | RLS (read-own-only, no direct writes), ledger uniqueness, squad = exactly 3, journal bound, trail once per date |
| Edge Functions | `deno test` | Replay victory/defeat, tampered action log rejected, duplicate `complete-trial` grants once, golden-vector parity |

## R21 — Local backend tooling

- **Finding**: Docker is installed; the Supabase CLI and Deno are not.
- **Decision**: The quickstart installs them (`brew install supabase/tap/supabase deno`). The backend lives at repo-root `supabase/`, the Supabase CLI convention, and runs locally with `supabase start`. Supabase is the already-recorded backend (ARCHITECTURE §7), so this is **not** a new stack choice.
