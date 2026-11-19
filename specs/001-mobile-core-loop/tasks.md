---

description: "Task list for the Mobile Core Loop"
---

# Tasks: Mobile Core Loop

**Input**: Design documents from `specs/001-mobile-core-loop/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: INCLUDED. The plan requires "dart unit tests for all domain rules first, widget tests for key screens", and SC-003..SC-006 require automated verification. Within each story, write the tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: the user story the task belongs to (US1, US2, US3)

## Path Conventions

| Prefix | Location |
|---|---|
| Mobile | `apps/mobile/lib/…`, tests in `apps/mobile/test/…` |
| Backend | `supabase/migrations/…`, `supabase/functions/…`, `supabase/tests/…` |
| Shared fixtures | `shared/game-vectors/…` |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, folder skeleton, tooling.

- [X] T001 Add the dependencies to `apps/mobile/pubspec.yaml`: `flutter_riverpod 3.3.2`, `go_router 17.2.3`, `supabase_flutter 2.18.3`, `camera 0.12.0+1`, `image_picker 1.2.2`, `geolocator 14.0.2`, `shared_preferences 2.5.5`, `uuid 4.6.0`, plus dev `mocktail 1.0.5` (`flutter pub add …`). Rename the package description from "A new Flutter project." to "Animon GO — mobile core loop".
- [X] T002 [P] Create the folder skeleton from plan.md: `apps/mobile/lib/app/`, `lib/core/game/`, `lib/features/exploration/classification/`, `test/core/game/`, `test/data/`, `test/features/`. Keep the existing per-folder `README.md` files.
- [X] T003 [P] Turn on strict analysis in `apps/mobile/analysis_options.yaml` (`strict-casts`, `strict-inference`, `strict-raw-types`, `prefer_final_locals`, `always_declare_return_types`) and confirm `flutter analyze` is clean.
- [X] T004 [P] Create `shared/game-vectors/` with a `README.md` stating the change rule from [contracts/game-rules-vectors.md](contracts/game-rules-vectors.md). Add empty `damage.json`, `variant.json`, `familiarity.json`, `battle.json` and `economy.json` files containing `[]`.
- [ ] T005 [P] Initialise the Supabase CLI project at the repo root (`supabase init`): `supabase/config.toml`, `supabase/migrations/`, `supabase/functions/`, `supabase/tests/`. Add `supabase/.env.example` listing variable names only, with no values.
- [ ] T006 [P] Add `scripts/check.sh` at the repo root. It runs `flutter analyze` and `flutter test` in `apps/mobile`, then, if the tools are installed, `deno test -A` in `supabase/functions` and `supabase test db`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The domain types, static data, repository seam, app shell and starter-account bootstrap that every story depends on.

**⚠️ CRITICAL**: No user-story work begins until this phase is complete.

- [X] T007 [P] Create the enums in `apps/mobile/lib/data/models/enums.dart`:
  - `Family {feline, canine, avian, rodent, insect}`
  - `Element {earth, fire, water, air, light, dark}`
  - `Rarity {common, uncommon, rare}`
  - `Attunement {day, rain, night}`
  - `AttunementSource {simulated}`
  - `FamiliarityTag {newEncounter, probablyFamiliar, returningPresence}`
  - `BattleAction {basic, skill, heal, guard}`
  - `BattleStatus {active, victory, defeat, abandoned}`
  - `TrailId {scan, bond, trial}`

  Each enum has `wireName` / `fromWire` that match the snake_case strings in [contracts/backend-api.md](contracts/backend-api.md).
- [X] T008 [P] Create the immutable `CreatureDefinition` in `apps/mobile/lib/data/models/creature.dart`, with fields `id, name, family, element, rarity, description, baseHp, attack, defense, speed, skillName, passiveName, spriteIndex, hue`.
- [X] T009 Create `apps/mobile/lib/core/constants/creatures.dart` with all **15** definitions copied verbatim from `animon-web/src/lib/data.ts` (read-only reference: names, stats, skills, passives, hues), plus `findCreature(id)`. Add `apps/mobile/test/core/constants/creatures_test.dart`, asserting "exactly 15 definitions" and unique IDs.
- [X] T010 [P] Create `apps/mobile/lib/core/constants/economy.dart` with the values from research R16:

  | Constant | Value |
  |---|---|
  | `trainCost` | 30 |
  | `trainBond` | 5 |
  | `discoverXp` | 50 |
  | `discoverEssence` | 15 |
  | `newCompanionBond` | 15 |
  | `ownedDiscoveryBond` | 15 |
  | `bondCap` | 100 |
  | `hpPerLevel` | 6 |
  | `atkPerLevel` | 2 |
  | `waveEssence` | 60 |
  | `waveXp` | 100 |
  | `xpPerPlayerLevel` | 250 |
  | `journalLimit` | 100 |
  | `encounterHistoryLimit` | 200 |
  | `starterEssence` | 240 |
  | `starterXp` | 120 |
  | `trailRewards` | {scan: 30, bond: 40, trial: 60} |
  | `dailyRewardedDiscoveryCap` | 20 |
  | `discoverPerHourLimit` | 30 |

  Also the starter set: mosslyn L5 bond 36 "Woodland trail", cindertail L4 bond 24 "Sunlit clearing", dewfin L3 bond 18 "Brookside path".
- [X] T011 [P] Create the immutable models in `apps/mobile/lib/data/models/`, with value equality and fields exactly as in [data-model.md](data-model.md) §3:
  - `owned_companion.dart`: `level` "(≥1)", `bond` "(0–100)"
  - `encounter.dart`: `lat?`/`lon?` "(3-dp rounded)", `isDemo`, `attunement`, `attunementSource`
  - `journal_entry.dart`
  - `trail_status.dart`
  - `player_state.dart`: includes `isLocalMode` and the derived `playerLevel`
- [X] T012 [P] Create the utilities:
  - `apps/mobile/lib/core/utils/clock.dart`: a `Clock` interface plus `SystemClock` and `FixedClock` for tests
  - `apps/mobile/lib/core/utils/geo.dart`: `roundCoord(double) → 3 dp` and `distanceMeters(lat1, lon1, lat2, lon2)`, using the prototype's equirectangular formula (111000 m per degree, longitude scaled by cos(lat))
  - `apps/mobile/lib/core/utils/request_id.dart`: UUID v4
- [ ] T013 Define the `GameRepository` interface in `apps/mobile/lib/data/repositories/game_repository.dart`. It mirrors every operation in [contracts/backend-api.md](contracts/backend-api.md): `bootstrapPlayer`, `getPlayerState`, `discover`, `trainCompanion`, `setSquad`, `startTrial`, `completeTrial`, `claimTrail`, `setTimezone`. Each reward call takes a `requestId`, and each response carries `PlayerState` plus `replayed`. Add typed errors (`GameError` with codes `LOW_CONFIDENCE, INVALID_INPUT, RATE_LIMITED, NOT_OWNED, INSUFFICIENT_ESSENCE, SQUAD_SIZE, SESSION_NOT_FOUND, SESSION_ABANDONED, INCOMPLETE_BATTLE, GOAL_NOT_MET, ALREADY_CLAIMED, INVALID_TIMEZONE, TIMEZONE_CHANGE_TOO_SOON`) and `NetworkError` (retryable).
- [ ] T014 Implement the `LocalGameRepository` skeleton in `apps/mobile/lib/data/repositories/local_game_repository.dart`:
  - in-memory player state plus a ledger map keyed by `(kind, instanceKey)` and by `requestId`, emulating `unique (player_id, kind, instance_key)` and `unique (player_id, request_id)`
  - `bootstrapPlayer`, granted once under ledger key `bootstrap`
  - `getPlayerState`
  - `setTimezone`, with the 24 h rule
  - the journal prepend helper that keeps the newest **100** entries

  Takes a `Clock`.
- [ ] T015 [P] Implement `SnapshotCache` in `apps/mobile/lib/data/repositories/snapshot_cache.dart`. It saves and loads the last `PlayerState` as JSON through `shared_preferences`, and is read-only offline (research R13).
- [ ] T016 [P] Create the theme in `apps/mobile/lib/core/theme/app_theme.dart`. Element colours come from `animon-web` `elementColor`: Earth #50824b, Fire #c57343, Water #418ea2, Air #719ba0, Light #ae9142, Dark #8975a6. Use Material 3, light and dark.
- [ ] T017 Create the providers in `apps/mobile/lib/app/providers.dart`:
  - `clockProvider`
  - `gameRepositoryProvider`: chooses `LocalGameRepository` or `SupabaseGameRepository` from `--dart-define=BACKEND` (default `local` in debug)
  - `playerStateProvider` (an `AsyncNotifier`): loads from the cache first, then refreshes from the repository
- [ ] T018 Create the app shell and routes in `apps/mobile/lib/app/app.dart` and `apps/mobile/lib/app/router.dart`. Routes: `/onboarding`, `/` (home), `/scan`, `/roster`, `/companion/:id`, `/squad`, `/trial`, `/journal`. Add a bottom navigation bar and a persistent banner reading "Local dev mode — progress not saved to server" when `isLocalMode`. Replace the counter demo in `apps/mobile/lib/main.dart` with `ProviderScope(child: AnimonApp())`.
- [ ] T019 Build the onboarding flow in `apps/mobile/lib/features/onboarding/onboarding_screen.dart`: a welcome screen, then `bootstrapPlayer(requestId, deviceTimezone)`, then the camera permission explanation, then the optional location explanation ("Location is optional and stored only approximately"), then home. Detect the device's IANA timezone with `DateTime.now().timeZoneName` and fall back to `"UTC"` when it isn't IANA.
- [ ] T020 [P] Add the migration `supabase/migrations/0001_core.sql` with the tables `players`, `owned_companions`, `squad_members`, `journal_entries` and `reward_ledger`, exactly as in [data-model.md](data-model.md) §4. It must include:
  - `check (essence >= 0)`, `check (xp >= 0)`
  - `check (level >= 1)`, `check (bond between 0 and 100)`
  - `check (slot between 0 and 2)`
  - `unique (player_id, creature_id)` on squad_members
  - `unique (player_id, kind, instance_key)` and `unique (player_id, request_id)` on reward_ledger
  - title "≤ 120 chars", detail "≤ 400 chars"
  - a deferred constraint trigger rejecting any commit that leaves a player with ≠ 3 squad rows

  Enable RLS with select-own-only policies and **no** insert/update/delete grants for `authenticated`.
- [ ] T021 Add the migration `supabase/migrations/0002_rpc_bootstrap_state.sql` with `security definer` RPCs:
  - `bootstrap_player(request_id, timezone, display_name)`: validates the timezone against `pg_timezone_names`; grants the starter set once (ledger `bootstrap`)
  - `get_player_state()`: returns the shape in contracts/backend-api.md, including `server_time` and `local_date = (now() at time zone timezone)::date`
  - `set_timezone(timezone)`: the 24 h rule
  - a journal trim trigger that keeps the newest 100 per player
- [ ] T022 [P] Add the pgTAP tests in `supabase/tests/core_test.sql`:
  - player A cannot select player B's rows
  - `authenticated` cannot insert into `reward_ledger` or `players`
  - `bootstrap_player` called twice grants once
  - the squad must have exactly 3 rows
  - the journal is trimmed to 100
- [ ] T023 Implement `SupabaseGameRepository` in `apps/mobile/lib/data/repositories/supabase_game_repository.dart` with `bootstrapPlayer`, `getPlayerState` and `setTimezone` over `supabase.rpc(...)`. Use anonymous sign-in (`auth.signInAnonymously()`) on first launch (research R15). Map HTTP 4xx to `GameError` and network failures or 5xx to `NetworkError`. Store `SUPABASE_URL` and `SUPABASE_ANON_KEY` from `--dart-define`, and never a service-role key.
- [ ] T024 [P] Add `apps/mobile/test/data/local_game_repository_test.dart`:
  - bootstrap gives 3 starters, squad = starters, 240 essence and 120 XP
  - a second bootstrap returns `replayed: true` with no extra grant
  - the journal is bounded to 100
  - a timezone change within 24 h fails with `TIMEZONE_CHANGE_TOO_SOON`

**Checkpoint**: the app launches in local mode, onboarding grants the starter roster, and the shell navigates. User stories can begin.

---

## Phase 3: User Story 1 — Discover and collect a companion (Priority: P1) 🎯 MVP

**Goal**: Capture → classify (mock) → soft fail or awakening reveal → companion in the roster, with a familiarity tag and no identity claims.

**Independent Test**: In local mode, capture and choose "Confident cat 0.92" with rain → Solcat is added to the roster. Capture and choose "Ambiguous 0.40" → a distinct "No confident match" screen, nothing awarded (quickstart rows 1–4).

### Tests for User Story 1 ⚠️ (write first, confirm they fail)

- [X] T025 [P] [US1] Fill `shared/game-vectors/variant.json` with all 15 (family × attunement) → creature_id cases from data-model §2, and `shared/game-vectors/familiarity.json` with:
  - the prototype `game.test.ts` cases
  - no-location fallback → `probablyFamiliar`, never `returningPresence`
  - more than 7 days → `newEncounter`
  - demo vs. real never match
  - different family → `newEncounter`
  - two prior matches with location inside the radius → `returningPresence`
  - one prior outside the family radius (Insect 60 m) → `newEncounter`
- [X] T026 [P] [US1] Add `apps/mobile/test/core/game/variant_test.dart` and `apps/mobile/test/core/game/familiarity_test.dart`, unit tests that load and assert the vectors from T025 (covers SC-005).
- [ ] T027 [P] [US1] Add `apps/mobile/test/features/exploration/discovery_controller_test.dart`:
  - a confident mock result (≥ 0.55) calls `repository.discover` with the same family and confidence
  - below the threshold or `family == null`, `discover` is **not** called and the state is `NoConfidentMatch` (SC-003)
  - the temp image file is deleted after `classify` returns **and** after it throws
  - a retry after `NetworkError` reuses the same `requestId`
- [ ] T028 [P] [US1] Add `apps/mobile/test/features/exploration/result_screen_test.dart`, a widget test: the success reveal and the soft-fail screen are visually distinct; a "Mock classifier" badge appears when the classifier id is `"mock"`; "Simulated attunement" is shown; no text contains "same animal", "recognised" or "identified" (FR-008).

### Implementation for User Story 1

- [X] T029 [P] [US1] Implement `chooseVariant(Family, Attunement) → CreatureDefinition` in `apps/mobile/lib/core/game/variant.dart`, using the table in data-model §2.
- [X] T030 [P] [US1] Implement `familiarity(Encounter current, List<Encounter> history) → FamiliarityTag` in `apps/mobile/lib/core/game/familiarity.dart`, following research R8:
  - a match needs the same family, `0 ≤ Δt < 7 days`, and the same `isDemo`
  - if both have coordinates, the distance must be below the family radius: Feline 200, Canine 300, Avian 120, Rodent 80, Insect 60 metres
  - if either lacks coordinates, family + recency is enough, but the result is **capped at probablyFamiliar**
  - more than 1 match with location → `returningPresence`; 1 match → `probablyFamiliar`; otherwise `newEncounter`
- [ ] T031 [P] [US1] Create the classification seam in `apps/mobile/lib/features/exploration/classification/`:
  - `family_classifier.dart`: the interface plus `ClassificationResult` and `CapturedImage`, per [contracts/family-classifier.md](contracts/family-classifier.md)
  - `classifier_thresholds.dart`: default 0.55 per family, overridable
  - `mock_family_classifier.dart`: `MockFamilyClassifier.scripted([...])` for tests, and a debug picker sheet with presets "Confident cat 0.92", "Confident dog 0.88", "Confident bird 0.85", "Ambiguous 0.40", "No animal"
- [ ] T032 [P] [US1] Create the location service in `apps/mobile/lib/services/location_service.dart`. It wraps `geolocator`: it asks permission only when requested, returns `null` when denied, unavailable or timed out (3 s), and returns coordinates already rounded to 3 dp (research R9).
- [ ] T033 [P] [US1] Create the camera service in `apps/mobile/lib/services/camera_service.dart`: live capture with `camera`, plus a photo fallback with `image_picker`. It returns a `CapturedImage` holding a temp path that the caller must delete (research R12). Add `NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription` and `NSPhotoLibraryUsageDescription` to `apps/mobile/ios/Runner/Info.plist`, and the CAMERA and ACCESS_COARSE_LOCATION permissions to `apps/mobile/android/app/src/main/AndroidManifest.xml`.
- [ ] T034 [US1] Implement `discover` in `LocalGameRepository` (`apps/mobile/lib/data/repositories/local_game_repository.dart`), following data-model §5:
  1. Reject a confidence below the threshold with `LOW_CONFIDENCE`.
  2. Apply the rate limit of 30 per hour (`RATE_LIMITED`).
  3. Resolve the variant, and compute familiarity against the last 7 days.
  4. Append the encounter, keeping the 200 most recent.
  5. Upsert the companion: new → L1, bond 15, context "Local discovery" (or "Sample woodland encounter" when it is a demo); already owned → +1 level, bond +15, capped at 100.
  6. Grant +15 essence and +50 XP under ledger `discovery:<requestId>` while under the cap of 20 per local day (`rewarded: false` after that).
  7. Add a journal entry: "A new chapter: {name}." or "{name}, a little closer."

  Depends on T029 and T030.
- [ ] T035 [US1] Implement `DiscoveryController` (an `AsyncNotifier`) in `apps/mobile/lib/features/exploration/discovery_controller.dart`:
  - flow: capture → classify → delete the temp file in `finally` → apply the threshold gate → `discover(requestId, family, confidence, attunement, attunementSource.simulated, location?, isDemo)`
  - states: `Idle`, `Capturing`, `Classifying`, `NoConfidentMatch`, `Revealed(creature, isNew, familiarity, rewarded)`, `Failed(retryable)`
  - Retry reuses the `requestId`

  Depends on T031–T034.
- [ ] T036 [US1] Build the scanner screen in `apps/mobile/lib/features/exploration/scan_screen.dart`: a camera preview, a capture button and a "Use a photo" fallback. The attunement selector defaults from the local hour (06:00–17:59 is day, otherwise night) and has a "Rain" toggle. Label it "Simulated attunement".
- [ ] T037 [US1] Build the result screens in `apps/mobile/lib/features/exploration/reveal_screen.dart`:
  - **awakening reveal**: creature name, element colour, rarity, "+50 XP · +15 essence" (or "Daily discovery rewards reached"), and the familiarity chip reading "New encounter" / "Probably familiar" / "Returning presence" with the helper text "Based on animal family, time and rough location — not individual recognition"
  - **soft-fail screen**: "No confident match — nothing awarded. Try a clearer view."
  - badges for "Mock classifier" and "Simulated attunement"
- [ ] T038 [P] [US1] Add the migration `supabase/migrations/0003_encounters.sql` with the `encounters` table from data-model §4:
  - `numeric(7,3)` lat/lon, "both null or both set"
  - `check (attunement_source = 'simulated')`
  - an index on (player_id, family, occurred_at desc)
  - trimming to the 200 most recent per player
- [ ] T039 [US1] Create the shared TS rules in `supabase/functions/_shared/`:
  - `creatures.ts`: the 15 definitions, the variant table and the radii, identical to the Dart
  - `familiarity.ts`
  - `vectors.test.ts`: loads `../../../shared/game-vectors/variant.json` and `familiarity.json`, and asserts the same expectations as T026
- [ ] T040 [US1] Create the Edge Function `supabase/functions/discover/index.ts`, following contracts/backend-api.md `discover`:
  - validate the JWT, the input, the threshold (0.55), `attunement_source == "simulated"`, and coordinates having ≤ 3 dp
  - apply the rate limit (30 per hour, counted from `encounters`)
  - in one transaction, through a service-role client inside the function only: insert the encounter, upsert the companion, write the ledger row `discovery:<request_id>` (daily cap 20), add the journal entry
  - a repeated `request_id` returns the stored `result` with `replayed: true`

  Add `supabase/functions/discover/index.test.ts`, covering: a duplicate request grants once, low confidence → 400, the 31st call within an hour → 429.
- [ ] T041 [US1] Implement `discover` in `SupabaseGameRepository` (`apps/mobile/lib/data/repositories/supabase_game_repository.dart`) via `functions.invoke('discover')`, mapping the errors to `GameError` and `NetworkError`.
- [ ] T042 [US1] Build the roster list in `apps/mobile/lib/features/collection/roster_screen.dart`: owned companions with name, element, level and bond, plus locked silhouettes for undiscovered variants with the hint "Try this family in a different attunement".

**Checkpoint**: US1 is fully playable in local mode, and against Supabase once T038–T041 are done. MVP demo-able.

---

## Phase 4: User Story 2 — Train a squad and win a trial (Priority: P2)

**Goal**: Spend essence to level up, keep exactly 3 in the squad, and play 3v3 waves whose reward is granted exactly once and verified by server replay.

**Independent Test**: With the 3 starters (granted at onboarding): train Mosslyn → L6 and −30 essence once; set the squad; win wave 1 → +60 essence and +100 XP once; a skill on cooldown is rejected without using a turn; losing all allies → defeat with no reward (quickstart rows 5–10, 15).

### Tests for User Story 2 ⚠️ (write first, confirm they fail)

- [X] T043 [P] [US2] Fill `shared/game-vectors/damage.json` with:
  - advantaged vs. neutral (×1.4)
  - guard halving
  - the floor of 4
  - Fire > Earth > Water > Fire, Air > Earth, Light ⇄ Dark
  - Earth attacking Air: neutral

  Fill `shared/game-vectors/battle.json` with:
  - a skill on cooldown: state unchanged, turn not advanced
  - heal capped at max HP, cooldown 3
  - skill power 1.65, cooldown 2
  - the target advances when an enemy dies
  - the active ally advances when an ally dies
  - a full victory and a full defeat with the starter squad at wave 1

  Fill `shared/game-vectors/economy.json` with:
  - train → +1 level, bond +5 capped at 100
  - `player_level(249)=1`, `player_level(250)=2`
  - `maxHp = base + (level−1)·6`, `effectiveAttack = atk + (level−1)·2`

  Generate the expected numbers by running the prototype formulas (research R19) by hand or in a scratch script. **Do not edit `animon-web`.**
- [X] T044 [P] [US2] Add the Dart vector tests in `apps/mobile/test/core/game/damage_test.dart`, `apps/mobile/test/core/game/battle_engine_test.dart` and `apps/mobile/test/core/game/economy_test.dart`, loading T043's files (covers FR-014..017).
- [ ] T045 [P] [US2] Add `apps/mobile/test/data/idempotency_test.dart` against `LocalGameRepository` (covers SC-004 and SC-006):
  - `trainCompanion` with the same `requestId` twice → deducted once
  - `INSUFFICIENT_ESSENCE` leaves the balance unchanged
  - `setSquad` with 2 or 4 or duplicate IDs → `SQUAD_SIZE`
  - `completeTrial` with the same session twice → one reward
  - a defeat replay → no reward
  - an incomplete action log → `INCOMPLETE_BATTLE`
  - `startTrial` with fewer than 3 owned → `SQUAD_SIZE`
- [ ] T046 [P] [US2] Add `apps/mobile/test/features/battle/trial_screen_test.dart`, a widget test: the skill button is disabled or ignored while on cooldown and the turn counter stays the same; the defeat screen shows no reward; the victory screen shows "+60 essence · +100 XP" only after `completeTrial` succeeds.

### Implementation for User Story 2

- [X] T047 [P] [US2] Implement the stats and training rules in `apps/mobile/lib/core/game/progression.dart`: `maxHp`, `effectiveAttack`, `playerLevel`, `applyTraining(OwnedCompanion) → +1 level, bond +5 capped at 100`, and `applyOwnedDiscovery`.
- [X] T048 [P] [US2] Implement `damage(attacker, attackerLevel, defender, {power, guard})` in `apps/mobile/lib/core/game/damage.dart`: `max(4, round((effAtk·power − def·0.3)·(adv?1.4:1)·(guard?0.5:1)))`, with `strongAgainst = {fire: earth, earth: water, water: fire, air: earth, light: dark, dark: light}`.
- [X] T049 [US2] Implement the deterministic battle engine in `apps/mobile/lib/core/game/battle_engine.dart`:
  - `createBattle(allies: [(id, level)]×3, wave)`, with enemies from `enemyTrio(wave)`: rotation `[[acornix, breezlet, petalume], [sparkit, dewfin, mistmoth], [zephruff, brookhound, mosslyn], [duskwing, moonchest, cindertail], [nightpurr, solcat, lumoth]][(wave−1) % 5]`. Enemy HP = base + (wave−1)·12 + slot·3; enemy level = wave.
  - `battleTurn(state, action)`, ported exactly from research R19, which returns the same instance for a rejected action. The log is capped at 12, and the accepted actions are recorded in `state.actions`.
  - `replay(snapshot, actions)`

  Depends on T047 and T048.
- [ ] T050 [US2] Implement `trainCompanion`, `setSquad`, `startTrial` and `completeTrial` in `LocalGameRepository` (`apps/mobile/lib/data/repositories/local_game_repository.dart`):
  - training costs 30 under ledger `train:<requestId>`
  - the squad must be exactly 3 distinct owned IDs
  - `startTrial` snapshots the squad levels and abandons any earlier active session
  - `completeTrial` replays from the **snapshot**: victory → ledger `wave:<sessionId>` (+60 essence, +100 XP) plus a journal entry "The woodland, wave {n}."; defeat → no reward; a still-active result → `INCOMPLETE_BATTLE`
- [ ] T051 [US2] Implement `BattleController` in `apps/mobile/lib/features/battle/battle_controller.dart`:
  - it holds `BattleState` and calls `battleTurn` locally
  - when the battle ends, it calls `completeTrial(sessionId, actions)`
  - if that fails with `NetworkError`, it adds `{sessionId, actions}` to `PendingCompletions`, persisted in `shared_preferences` at `apps/mobile/lib/features/battle/pending_completions.dart`
  - pending completions are retried at app start and on resume (research R13)
- [ ] T052 [US2] Build the trial screen in `apps/mobile/lib/features/battle/trial_screen.dart`:
  - three allies and three enemies with HP bars
  - an active-ally highlight and a target picker
  - the action buttons Attack / Skill (with a cooldown badge) / Renewal heal (with a cooldown badge) / Guard
  - the last 4 log lines
  - victory and defeat panels
  - entry is blocked with "You need a squad of three to enter a trial" when the squad has fewer than 3 (SC-006)
- [ ] T053 [P] [US2] Build the companion detail screen in `apps/mobile/lib/features/collection/companion_screen.dart`: stats at the current level, skill, passive, bond, and a "Train · 30 essence" button that is disabled when essence < 30. Training calls `trainCompanion(requestId, id)` with a retry that reuses the `requestId`.
- [ ] T054 [P] [US2] Build the squad screen in `apps/mobile/lib/features/collection/squad_screen.dart`. The player picks exactly 3 from the roster, and Save is disabled unless exactly 3 distinct companions are selected. It calls `setSquad`.
- [ ] T055 [P] [US2] Add the migration `supabase/migrations/0004_trials_training.sql`:
  - the `battle_sessions` table from data-model §4: `check (wave >= 1)`, `squad_snapshot jsonb`, status active/victory/defeat/abandoned
  - the RPCs `train_companion(request_id, creature_id)`, `set_squad(creature_ids)` and `start_trial(request_id, wave)`, following contracts/backend-api.md

  Add `supabase/tests/trials_test.sql` (pgTAP): training twice with the same request_id deducts once; insufficient essence → error with no change; `set_squad` with ≠ 3 → `SQUAD_SIZE`.
- [ ] T056 [US2] Port the battle engine to TS in `supabase/functions/_shared/battle.ts` (`damage`, `enemyTrio`, `createBattle`, `battleTurn`, `replay`), mirroring T048–T049. Extend `supabase/functions/_shared/vectors.test.ts` to assert `damage.json`, `battle.json` and `economy.json`.
- [ ] T057 [US2] Create the Edge Function `supabase/functions/complete-trial/index.ts`, following contracts/backend-api.md:
  - load the session (owned by the caller), and reject more than 500 actions
  - replay from `squad_snapshot`
  - victory → session = victory, ledger `wave:<session_id>`, journal entry; defeat → session = defeat; still active → 400 `INCOMPLETE_BATTLE`
  - a terminal session returns the stored outcome with `replayed: true`

  Add `supabase/functions/complete-trial/index.test.ts`: a duplicate completion grants once; a tampered log that ends in defeat earns no reward; a session abandoned in favour of a newer one → 409.
- [ ] T058 [US2] Implement `trainCompanion`, `setSquad`, `startTrial` and `completeTrial` in `SupabaseGameRepository` (`apps/mobile/lib/data/repositories/supabase_game_repository.dart`).

**Checkpoint**: US1 and US2 both work independently. The full discover → train → battle loop is playable.

---

## Phase 5: User Story 3 — Keep coming back (Priority: P3)

**Goal**: Daily trails, each claimable once per server-determined local date, and a field journal bounded to 100 entries.

**Independent Test**: After a discovery, claim "scan" → +30 essence; a second claim → "Already claimed today"; moving the device clock forward still refuses the claim; 101 journal events → 100 kept (quickstart rows 11–13).

### Tests for User Story 3 ⚠️ (write first, confirm they fail)

- [ ] T059 [P] [US3] Add `apps/mobile/test/data/trails_test.dart` against `LocalGameRepository` with a `FixedClock`:
  - `scan`'s goal is not met before a discovery → `GOAL_NOT_MET`
  - after a discovery the claim grants 30 once
  - the same date with a different requestId → `ALREADY_CLAIMED`
  - advancing the `FixedClock` past local midnight in the player's timezone allows a claim again
  - a changed *device* time doesn't affect the server date in local mode, because the repository uses its own clock
  - `bond` needs a repeat-family discovery today; `trial` needs a cleared wave today
- [ ] T060 [P] [US3] Add `apps/mobile/test/features/profile/journal_screen_test.dart`, a widget test: entries are newest first; 101 inserted → 100 shown, with the oldest gone.

### Implementation for User Story 3

- [ ] T061 [US3] Implement the trail rules in `apps/mobile/lib/core/game/trails.dart`. `trailGoals(encountersToday, wavesClearedToday)` gives: `scan`: ≥ 1 encounter today; `bond`: ≥ 1 encounter today whose family has an earlier encounter; `trial`: ≥ 1 victory today. `localDate(DateTime utcNow, String timezone)` uses the timezone database. If that needs the `timezone` package, add it to `apps/mobile/pubspec.yaml` and note it in research.md.
- [ ] T062 [US3] Implement `claimTrail` and the trail status in `getPlayerState` in `LocalGameRepository` (`apps/mobile/lib/data/repositories/local_game_repository.dart`), under ledger key `trail:<trailId>:<localDate>` with rewards scan 30, bond 40, trial 60.
- [ ] T063 [P] [US3] Build the daily trails card in `apps/mobile/lib/features/profile/trails_card.dart`, shown on home. Each of the 3 trails shows its progress, its reward, and a Claim button: disabled when the goal isn't met, "Claimed today" once claimed. Claiming reuses the `requestId` on retry.
- [ ] T064 [P] [US3] Build the journal screen in `apps/mobile/lib/features/profile/journal_screen.dart`: a newest-first list with an element-coloured accent, a title, a detail line and a relative time.
- [ ] T065 [US3] Add the migration `supabase/migrations/0005_trails.sql`: the RPC `claim_trail(request_id, trail_id)`, which computes `local_date = (now() at time zone players.timezone)::date` and checks the goal from `encounters` and `battle_sessions` for that date. Extend `get_player_state` with the `trails` array. Add `supabase/tests/trails_test.sql` (pgTAP): a claim works once per date; a different request_id on the same date → `ALREADY_CLAIMED`; an unmet goal → `GOAL_NOT_MET`.
- [ ] T066 [US3] Implement `claimTrail` in `SupabaseGameRepository` (`apps/mobile/lib/data/repositories/supabase_game_repository.dart`).

**Checkpoint**: all three user stories work independently.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T067 [P] Add the offline experience in `apps/mobile/lib/app/offline_banner.dart` and `apps/mobile/lib/app/providers.dart`: detect a `NetworkError`, show the "Offline — showing last synced progress" banner, keep cached state read-only, and give every reward action a visible failure with Retry (NFR-AVAIL-1, quickstart row 14).
- [ ] T068 [P] Record the familiarity no-location rule (research R8: family + recency fallback, capped at "Probably familiar") in `docs/decisions/2026-11-09-familiarity-without-location.md`, and update the ported-algorithm text in `docs/PRD.md` §6 to match.
- [ ] T069 [P] Update `apps/mobile/README.md` with: how to run in local and Supabase modes, the `--dart-define` flags, the test commands, and the fact that the classifier is a mock behind `FamilyClassifier`.
- [ ] T070 Run every scenario in [quickstart.md](quickstart.md) on an Android device and an iOS simulator or device, and record the results (pass/fail per row) in `specs/001-mobile-core-loop/checklists/quickstart-results.md`.
- [ ] T071 Measure cold start and the battle-screen frame rate on the reference low-end Android device (`flutter run --profile`, DevTools). Record the numbers in `docs/SRS.md` NFR-PERF-1. Don't claim targets that weren't measured.
- [ ] T072 Run `scripts/check.sh` (analyze, flutter test, deno test, pgTAP) and fix any failures until everything is green.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup. **Blocks every user story.**
- **US1 (Phase 3)**: depends only on Foundational.
- **US2 (Phase 4)**: depends only on Foundational, because the starter squad from T019/T021 gives three companions without needing a US1 discovery. It shares `LocalGameRepository` and `SupabaseGameRepository` files with US1, so tasks touching those files run one at a time.
- **US3 (Phase 5)**: depends on Foundational. Its goal checks read encounters and sessions, so a full end-to-end check of `scan`/`bond`/`trial` needs US1 and US2. The unit tests (T059) seed that state directly.
- **Polish (Phase 6)**: after the stories you intend to ship.

### Within each story

1. Vectors and tests, which must fail first.
2. Pure rules in `lib/core/game/`.
3. `LocalGameRepository`.
4. Controller.
5. Screens.
6. Backend migration.
7. TS port and Edge Function.
8. `SupabaseGameRepository`.

### Parallel opportunities

- **Setup**: T002–T006.
- **Foundational**: T007, T008, T010, T011, T012, T015, T016, T020, T022, T024, once their inputs exist.
- **US1**: tests T025–T028 together; then T029–T033 together; and T038 (migration) alongside the mobile work.
- **US2**: tests T043–T046 together; then T047 and T048 together; T053, T054 and T055 together.
- **US3**: T059 and T060 together; T063 and T064 together.
- **Across stories**: once Phase 2 is done, US1, US2 and US3 rule and screen work can go in parallel. The shared repository files are the serialization point.

---

## Parallel Example: User Story 1

```text
# Tests first (together):
T025 Fill variant.json + familiarity.json
T026 variant_test.dart + familiarity_test.dart
T027 discovery_controller_test.dart
T028 result_screen_test.dart

# Then independent building blocks (together):
T029 core/game/variant.dart
T030 core/game/familiarity.dart
T031 classification seam + MockFamilyClassifier
T032 services/location_service.dart
T033 services/camera_service.dart (+ platform permission strings)
```

## Parallel Example: User Story 2

```text
T043 damage.json + battle.json + economy.json
T044 damage/battle/economy Dart tests
T045 idempotency_test.dart
T046 trial_screen_test.dart
# then
T047 progression.dart   |   T048 damage.dart
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Phase 1 → Phase 2. The app launches with the starter roster in local mode.
2. Phase 3 (US1), mobile tasks T025–T037 and T042, playable in **local mode**.
3. **Stop and validate**: quickstart rows 1–4 on a real phone with the mock classifier.
4. Then the US1 backend (T038–T041) to make discovery server-authoritative.

### Incremental delivery

1. US1 → demo the discovery moment.
2. US2 → demo training plus a full trial win, with the reward verified by replay.
3. US3 → daily trails and the journal.
4. Polish → offline mode, decision note, device measurements.

The real classifier (ML Kit or SigLIP 2) is **not** a task here. It replaces `MockFamilyClassifier` behind `FamilyClassifier` after `docs/research/model-evaluation-plan.md` step 6, with no change to callers.

---

## Notes

- **[P]** = different files with no incomplete dependency. Tasks on `local_game_repository.dart` / `supabase_game_repository.dart` are never [P] with each other.
- Every game-constant change updates `shared/game-vectors/` in the same change (contracts/game-rules-vectors.md).
- `animon-web/` is read-only; it is ported from, never edited (AGENTS.md).
- Commit after each task or logical group, and stop at any checkpoint to validate the story on its own.
