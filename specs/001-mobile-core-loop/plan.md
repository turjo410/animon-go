# Implementation Plan: Mobile Core Loop

**Branch**: `001-mobile-core-loop` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-mobile-core-loop/spec.md`

## Summary

Build the Animon GO MVP loop as a native Flutter app with these steps:

1. **Discover** — capture a photo, classify its animal family, resolve one of 15 elemental variants, and tag familiarity.
2. **Collect** — the companion joins the roster.
3. **Train** — level companions up and keep a 3-member squad.
4. **Battle** — turn-based 3v3 PvE waves.
5. **Return** — daily trails and a bounded journal.

The technical approach:

- **Game rules.** All rules are ported from the `animon-web` prototype into **pure Dart** (`lib/core/game/`). They are mirrored in **TypeScript** for server-side checks, and **shared golden vectors** keep the two identical.
- **Server authority.** Supabase is the source of truth. Postgres RPCs handle simple reward operations, and Edge Functions handle `discover` and `complete-trial`. A trial is validated by **deterministic replay** of the client's action log. Every reward goes through one `reward_ledger` whose unique keys guarantee "at most once".
- **Classification seam.** Classification sits behind a `FamilyClassifier` interface. This feature ships a deterministic **mock**; the real model plugs in later without touching callers.
- **Local dev mode.** A `LocalGameRepository` makes the whole loop playable before the backend exists.

## Technical Context

**Language/Version**:
- Dart 3.9.2 / Flutter 3.35.4 (mobile)
- TypeScript on Deno 2.x (Supabase Edge Functions)
- SQL / PL/pgSQL on Postgres 15+ (Supabase)

**Primary Dependencies**:
- Mobile: flutter_riverpod 3.3.2, go_router 17.2.3, supabase_flutter 2.18.3, camera 0.12.0+1, image_picker 1.2.2, geolocator 14.0.2, shared_preferences 2.5.5, uuid 4.6.0
- Dev: mocktail 1.0.5
- Backend: Supabase CLI

**Storage**: Supabase Postgres, the authoritative store (data-model §4). On the device, a `shared_preferences` JSON snapshot for read-only offline viewing. Captured images are never stored.

**Testing**: `flutter test` (unit, notifier and widget), `deno test` (Edge Functions and vector parity), `supabase test db` (pgTAP: RLS and constraints).

**Target Platform**: iOS 15+ and Android 8.0+ (API 26+), phones.

**Project Type**: Mobile app plus a BaaS backend (Supabase: migrations, RPCs, Edge Functions).

**Performance Goals**:
- Battle screen at 60 fps on the reference device.
- Mock discovery: capture to reveal in ≤ 1 s, excluding animation.
- Real-classifier latency (NFR-LAT-1, ≤ 1.5 s) is measured later, when the model plugs in. It is not claimed here.
- Cold start target: ≤ 3 s on a low-end Android reference device. This defines NFR-PERF-1 and must be measured before it is claimed.

**Constraints**:
- Reward operations are idempotent (NFR-REL-1).
- Read-only use offline; server actions fail visibly (NFR-AVAIL-1).
- No raw image persisted (FR-004).
- Location is opt-in and rounded to 3 dp (FR-009).
- The daily boundary comes from server time in the player's timezone (FR-020).
- The client never computes balances.

**Scale/Scope**:
- MVP and internal testers; design ceiling ~10k players.
- 15 static creatures; 5 enemy trios.
- About 8 screens: onboarding, home, scanner/reveal, roster, companion detail, squad, trial, journal/trails.

All Technical Context items are resolved. There is no remaining NEEDS CLARIFICATION; see [research.md](research.md) R1–R21.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | How this plan complies |
|---|---|---|
| I. Mobile-first, native product | ✅ | Flutter in `apps/mobile`. `animon-web` was only read, for porting. Camera and GPS are first-class inputs. |
| II. Spec before code | ✅ | This plan follows spec → plan; `/speckit-tasks` comes next. One spec-vs-prototype conflict (familiarity without location) is resolved in favour of the spec and flagged for a decision note (R8). |
| III. Identity ≠ familiarity (NON-NEGOTIABLE) | ✅ | Familiarity is a family + recency + approximate-distance heuristic. A UI copy rule forbids "same animal / recognised / identified" (contracts/backend-api.md). No identity pilot code is involved. |
| IV. Server is the authority | ✅ | All essence and XP changes happen server-side (RPC / Edge). Trial wins are verified by replay against a server snapshot (R4). The ledger's unique keys provide idempotency (R6). |
| V. One claim per real animal | ✅ N/A | This feature makes no exclusive per-animal claims. Roster ownership is per *creature definition*, not per real animal. |
| VI. Privacy and consent | ✅ | Images stay on the device and are deleted after classification (R12). Location is opt-in and rounded to 3 dp (R9). Only the public anon key is in the client (SEC-4). The consent and retention policy remains a gate before *public beta*; it doesn't block this internal MVP. |
| VII. Small, evidence-driven scope (NON-NEGOTIABLE) | ✅ | No model training: classification is mocked behind a seam (R11). No AR, multiplayer or monetization. Weather stays simulated (R10). |

**Gate result (pre-research)**: PASS. **Re-check after Phase 1 design**: PASS. The design added no new principle risks; the one deliberate complexity is justified below.

## Project Structure

### Documentation (this feature)

```text
specs/001-mobile-core-loop/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 — decisions R1–R21
├── data-model.md        # Phase 1 — domain types, tables, ledger, state transitions
├── quickstart.md        # Phase 1 — runnable validation scenarios
├── contracts/
│   ├── backend-api.md         # RPCs + Edge Functions, idempotency, errors
│   ├── family-classifier.md   # device-side model seam (mock now)
│   └── game-rules-vectors.md  # Dart ⇄ TS parity fixtures
├── checklists/requirements.md
└── tasks.md             # Phase 2 — created by /speckit-tasks
```

### Source Code (repository root)

```text
apps/mobile/
├── lib/
│   ├── main.dart                       # bootstrap, ProviderScope, BACKEND dart-define
│   ├── app/                            # MaterialApp.router, go_router routes, shell
│   ├── core/
│   │   ├── constants/                  # creatures.dart, variants, economy, radii, rotation
│   │   ├── game/                       # PURE DART rules: variant, familiarity, damage,
│   │   │                               #   battle engine, training, rewards, journal bound
│   │   ├── theme/                      # element colours, typography
│   │   └── utils/                      # rounding, clock abstraction, request ids
│   ├── data/
│   │   ├── models/                     # Family, Element, Creature, OwnedCompanion, Encounter,
│   │   │                               #   PlayerState, BattleState, JournalEntry, TrailStatus
│   │   └── repositories/
│   │       ├── game_repository.dart          # interface (mirrors contracts/backend-api.md)
│   │       ├── local_game_repository.dart    # in-memory "server" for dev/tests (R14)
│   │       ├── supabase_game_repository.dart
│   │       └── snapshot_cache.dart           # offline read-only cache (R13)
│   ├── services/                       # supabase client, location (geolocator), camera
│   └── features/
│       ├── onboarding/                 # first run: anonymous auth, bootstrap, permissions
│       ├── exploration/                # scanner, capture, classification seam, reveal
│       │   └── classification/         # FamilyClassifier, MockFamilyClassifier, thresholds
│       ├── collection/                 # roster, companion detail, training, squad
│       ├── battle/                     # trial screen, battle controller, pending completions
│       └── profile/                    # journal, daily trails, settings
└── test/
    ├── core/game/                      # rule unit tests + vectors_test.dart
    ├── data/                           # repository + idempotency tests
    └── features/                       # notifier and widget tests

supabase/                               # Supabase CLI project (backend already decided; ARCHITECTURE §7)
├── config.toml
├── migrations/                         # tables, RLS, ledger, RPCs, triggers
├── tests/                              # pgTAP
└── functions/
    ├── _shared/                        # creatures.ts, game engine (TS port), vectors.test.ts
    ├── discover/
    └── complete-trial/

shared/
└── game-vectors/                       # *.json golden cases used by Dart AND Deno tests
```

**Structure Decision**: The mobile code follows the feature-first layout already scaffolded in `apps/mobile/lib/` (AGENTS.md, ARCHITECTURE §3). Discovery and capture live in `features/exploration/`. `features/identity/` stays reserved for the separate identity pilot boundary and is untouched by this feature.

The backend is a standard Supabase CLI project at the repo root, `supabase/`. `shared/game-vectors/` sits at the root because two toolchains (Flutter and Deno) consume it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| The game engine exists twice (Dart client + TypeScript server) | The server must verify trial wins without trusting the client (constitution IV, FR-019), and Supabase Edge Functions run TypeScript, not Dart | A server round-trip per turn adds latency to every tap and breaks on weak networks. Trusting a client "won" flag violates constitution IV. Drift risk is contained by the shared golden vectors (R5) |
| Two repository implementations (local + Supabase) | The full loop must be playable and widget-testable before and without a backend (R14) | Mocking Supabase per test is brittle and gives no playable dev build. ARCHITECTURE §3 already prescribes "one interface, swappable" |

## Next step

Run `/speckit-tasks` to break this plan into ordered tasks. Suggested order:
1. Domain rules and vectors.
2. Local repository, then the screens (playable in local mode).
3. Supabase migrations and RPCs.
4. Edge Functions.
5. The Supabase repository wiring.
