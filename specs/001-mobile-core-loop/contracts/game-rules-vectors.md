# Contract — Shared game-rule golden vectors

**Location**: `shared/game-vectors/` (repo root)
**Consumers**:
- Dart: `apps/mobile/test/core/game/vectors_test.dart`
- TypeScript: `supabase/functions/_shared/vectors.test.ts`

**Purpose**: The Dart engine (client) and the TypeScript engine (server replay, research R4) must give **identical** results. Both test suites load these files, so any divergence fails CI on whichever side is wrong (R5).

## Files and shapes

Each file is a JSON array of cases: `{ "name": string, "input": {...}, "expected": {...} }`.

| File | Input | Expected |
|---|---|---|
| `damage.json` | `{ attacker_id, attacker_level, defender_id, power, guard }` | `{ damage }` |
| `variant.json` | `{ family, attunement }` | `{ creature_id }` |
| `familiarity.json` | `{ current: Encounter, history: Encounter[] }`, where times are epoch ms and lat/lon are optional | `{ tag }` |
| `battle.json` | `{ allies: [{id, level}]×3, wave, actions: [action...] }` | `{ status, turn, allies_hp[3], enemies_hp[3], cooldowns[3][2], active, target }` |
| `economy.json` | `{ op: "train"\|"discover_new"\|"discover_owned"\|"wave"\|"player_level", ...args }` | resulting values |

## Required cases (minimum)

- **damage**:
  - advantaged vs. neutral, showing the ×1.4 ratio (FR-015)
  - guard halving
  - the floor of 4
  - Air > Earth
  - Light ⇄ Dark
  - Earth attacking Air: no advantage
- **variant**: all 15 (family × attunement) pairs (FR-005).
- **familiarity**: the prototype `game.test.ts` cases, plus
  - no-location fallback → `probablyFamiliar`, never `returningPresence` (R8)
  - more than 7 days → `newEncounter`
  - demo vs. real never match
  - two prior matches with location → `returningPresence`
- **battle**:
  - a skill on cooldown leaves the state unchanged and does not advance the turn (US2 scenario 3)
  - heal capped at max HP
  - a full victory sequence
  - a full defeat sequence (FR-017)
  - the target advances when an enemy falls
- **economy**:
  - train +1 level, bond +5 capped at 100
  - discovering an owned creature: +1 level, bond +15 capped
  - `player_level(249) = 1`, `player_level(250) = 2`

## Change rule

Changing any game constant or formula means updating these vectors in the **same** change. Both suites must pass before merge.
