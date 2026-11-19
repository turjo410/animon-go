# Quickstart — validating the Mobile Core Loop

This guide shows how to prove the feature works end-to-end. Contracts and data shapes are described in [contracts/](contracts/) and [data-model.md](data-model.md) and are not repeated here.

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Flutter / Dart | 3.35.4 / 3.9.2 (FVM default) | already installed |
| Xcode (iOS) / Android Studio (Android) | current | for device or simulator runs |
| Docker | running | already installed |
| Supabase CLI | latest | `brew install supabase/tap/supabase` |
| Deno | 2.x | `brew install deno` |

## A. Local dev mode (no backend; available after the domain and UI tasks)

```sh
cd apps/mobile
flutter pub get
flutter test                                  # domain rules, golden vectors, notifiers, widgets
flutter run --dart-define=BACKEND=local       # the whole loop, in-memory "server"
```

**Expected**: the app opens with the banner "Local dev mode — progress not saved to server" and the 3 starter companions (Mosslyn L5, Cindertail L4, Dewfin L3), 240 essence and 120 XP.

## B. With the local Supabase stack

```sh
supabase start                                # from repo root; prints the API URL + anon key
supabase db reset                             # applies supabase/migrations
supabase test db                              # pgTAP: RLS, ledger uniqueness, squad = 3, journal bound
supabase functions serve                      # discover, complete-trial
(cd supabase/functions && deno test -A)       # replay + golden-vector parity
cd apps/mobile && flutter run \
  --dart-define=BACKEND=supabase \
  --dart-define=SUPABASE_URL=<printed url> \
  --dart-define=SUPABASE_ANON_KEY=<printed anon key>
```

The anon key is public by design and gives only RLS-limited access. No service-role key is ever passed to the app (SEC-4).

## Validation scenarios (map to the spec)

| # | Do | Expect | Covers |
|---|---|---|---|
| 1 | Fresh install → allow camera → capture → mock sheet: "Confident cat 0.92", attunement **rain** | Awakening reveal for **Solcat**; roster gains Solcat L1; "+50 XP · +15 essence"; badges show "Mock classifier" and "Simulated attunement" | US1-1, FR-005/006, SC-001 |
| 2 | Capture → "Ambiguous 0.40" | A distinct "No confident match" screen; nothing awarded; no network call made | US1-2, FR-003, SC-003 |
| 3 | With location allowed, discover a Feline twice at the same spot | 2nd: "Probably familiar"; 3rd: "Returning presence"; copy never says "same animal" | US1-3, FR-007/008 |
| 4 | Deny location → discover a Feline twice | 2nd tagged "Probably familiar" (fallback, capped; R8); discovery itself works | US1-4, FR-009 |
| 5 | Train Mosslyn with ≥ 30 essence | L5 → L6, HP +6, ATK +2, essence −30 exactly once. Toggle airplane mode mid-request, then Retry: still deducted once | US2-1, FR-011, SC-004 |
| 6 | Set a squad of 3 | Exactly 3 active; trying 2 or 4 is impossible in the UI and rejected by the server | US2-2, FR-012, SC-006 |
| 7 | In a trial, use a skill, then tap skill again next turn | Second tap rejected; turn counter unchanged | US2-3, FR-014 |
| 8 | Fire attacker vs. Earth target, compared with a neutral target | Damage ×1.4 (exact values in `shared/game-vectors/damage.json`) | US2-4, FR-015 |
| 9 | Clear wave 1 → kill the app before the reward shows → reopen | Reward granted exactly once (+60 essence, +100 XP); the queued completion retries with the same session_id | US2-5, FR-016, SC-004 |
| 10 | Lose all 3 allies | Defeat screen; no reward | US2-6, FR-017 |
| 11 | After a discovery, claim the "scan" trail; claim again | First: +30 essence; second: "Already claimed today" | US3-1, FR-020 |
| 12 | Change the device clock +1 day and claim again | Still refused (the server date decides) | edge case: clock disagreement |
| 13 | Make 101 journal events (via a test helper) | 100 entries kept; the oldest dropped | US3-2, FR-021 |
| 14 | Airplane mode → open the app | Last synced state shown with an "Offline" banner; train / claim / discover fail visibly with Retry | NFR-AVAIL-1 |
| 15 | Fewer than 3 owned (test account) → open Trials | Entry blocked with an explanation | edge case, SC-006 |

## Automated equivalents

- **Dart**: `flutter test` covers rows 2, 5 (logic), 6–8, 10 and 13, plus golden-vector parity.
- **Deno**: `deno test` covers 9 (replay, duplicate completion) and tampered or incomplete action logs.
- **pgTAP**: `supabase test db` covers 5–6, 11–13 at the database level, and RLS ("player A cannot read B; nobody can insert into reward_ledger directly").
