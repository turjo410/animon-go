# Data Model — Mobile Core Loop (Phase 1)

**Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

There are two layers:
- **Client domain types**: pure Dart, in `apps/mobile/lib/data/models/`.
- **Server tables**: Postgres in Supabase, under `supabase/migrations/`.

Static creature data is code, not a table.

---

## 1. Enumerations

| Enum | Values | Source |
|---|---|---|
| `Family` | feline, canine, avian, rodent, insect | FR-002 |
| `Element` | earth, fire, water, air, light, dark | PRD §6 |
| `Rarity` | common, uncommon, rare | data.ts |
| `Attunement` | day, rain, night | FR-005 |
| `AttunementSource` | simulated *(real is reserved for Phase 4; rejected by the server in this feature)* | FR-006 |
| `FamiliarityTag` | newEncounter, probablyFamiliar, returningPresence | FR-007 |
| `BattleAction` | basic, skill, heal, guard | FR-014 |
| `BattleStatus` | active, victory, defeat, abandoned | FR-016/017 |
| `TrailId` | scan, bond, trial | research R17 |
| `RewardKind` | discovery, train, wave, trail, bootstrap | ledger keys |

## 2. Static: CreatureDefinition (15 entries, shared by every player)

**Fields**:
- `id` (slug), `name`, `family`, `element`, `rarity`, `description`
- `baseHp`, `attack`, `defense`, `speed`
- `skillName`, `passiveName`, `spriteIndex`, `hue`

**Values**: copied verbatim from [`animon-web/src/lib/data.ts`](../../animon-web/src/lib/data.ts) into `lib/core/constants/creatures.dart`, and into `supabase/functions/_shared/creatures.ts`. The two are kept identical by the golden vectors.

**Variant table** (FR-005; deterministic, each family × attunement maps to exactly one creature):

| Family | day | rain | night |
|---|---|---|---|
| Feline | mosslyn | solcat | nightpurr |
| Canine | cindertail | brookhound | zephruff |
| Avian | breezlet | dewfin | duskwing |
| Rodent | acornix | sparkit | moonchest |
| Insect | petalume | mistmoth | lumoth |

**Validation**: exactly 15 definitions; every (family, attunement) pair resolves to exactly one ID; IDs are unique.

## 3. Client domain types

| Type | Fields | Notes |
|---|---|---|
| `ClassificationResult` | `family?`, `confidence` (0–1), `isConfident` | `family == null` or `!isConfident` means a soft fail (FR-003) |
| `OwnedCompanion` | `creatureId`, `level` (≥1), `bond` (0–100), `discoveredContext` (string), `acquiredAt` | One per (player, creature) |
| `Encounter` | `family`, `occurredAt`, `lat?`, `lon?` (3-dp rounded), `isDemo`, `attunement`, `attunementSource` | Input to familiarity |
| `Squad` | `members: List<String>` (exactly 3 distinct owned IDs) | FR-012 |
| `PlayerState` | `essence`, `xp`, `playerLevel` (derived), `roster`, `squad`, `journal`, `trailStatus`, `snapshotAt`, `isLocalMode` | View over server state (FR-018) |
| `BattleUnit` | `creatureId`, `level`, `hp`, `maxHp`, `cooldowns (skill, heal)` | |
| `BattleState` | `sessionId`, `wave`, `turn`, `allies[3]`, `enemies[3]`, `activeAlly`, `target`, `guardUp`, `status`, `log` (≤12), `actions` (recorded for replay) | Immutable; `battleTurn` returns a new value |
| `JournalEntry` | `id`, `title`, `detail`, `element`, `occurredAt` | Newest first, ≤100 |
| `TrailStatus` | per `TrailId`: `goalMet`, `claimedToday`, `reward` | Computed server-side |

## 4. Server tables (Postgres)

All tables have RLS enabled. Players may `select` only their own rows (`player_id = auth.uid()`). There are **no** direct client `insert`/`update`/`delete` grants; writes go only through the RPCs and Edge Functions in [contracts/backend-api.md](contracts/backend-api.md).

### `players`
| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | = `auth.users.id` |
| `display_name` | text | default 'Explorer', length 1–24 |
| `essence` | int | `check (essence >= 0)` |
| `xp` | int | `check (xp >= 0)` |
| `timezone` | text | valid IANA name (checked against `pg_timezone_names`) |
| `timezone_changed_at` | timestamptz | change allowed only if > 24 h ago (R7) |
| `created_at` | timestamptz | |

### `owned_companions`
| Column | Type | Rules |
|---|---|---|
| `player_id` | uuid FK → players | |
| `creature_id` | text | `check` in the 15 IDs |
| `level` | int | `check (level >= 1)` |
| `bond` | int | `check (bond between 0 and 100)` |
| `discovered_context` | text | |
| `acquired_at` | timestamptz | |
| | | **PK (player_id, creature_id)** |

### `squad_members`
| Column | Type | Rules |
|---|---|---|
| `player_id` | uuid | |
| `slot` | smallint | `check (slot between 0 and 2)` |
| `creature_id` | text | FK → owned_companions(player_id, creature_id) |
| | | **PK (player_id, slot)**; **unique (player_id, creature_id)** |

"Exactly three" (FR-012, SC-006) is enforced by `set_squad` replacing all 3 rows in one transaction, plus a deferred constraint trigger that rejects a commit leaving a player with ≠ 3 rows.

### `encounters`
| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | |
| `player_id` | uuid | |
| `family` | text | enum check |
| `occurred_at` | timestamptz | server `now()` — the client time is ignored |
| `lat`, `lon` | numeric(7,3) null | already rounded; both null or both set |
| `is_demo` | bool | |
| `attunement` | text | enum |
| `attunement_source` | text | `check (attunement_source = 'simulated')` in this feature |
| `creature_id` | text | resolved variant |
| `familiarity` | text | enum, computed server-side |
| | | Index (player_id, family, occurred_at desc); history pruned to the 200 most recent per player |

### `battle_sessions`
| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | the wave **instance** (FR-016) |
| `player_id` | uuid | |
| `wave` | int | `check (wave >= 1)` |
| `squad_snapshot` | jsonb | `[{creature_id, level}] ×3`, frozen at start |
| `status` | text | active → victory / defeat / abandoned |
| `action_count` | int | stored after replay |
| `started_at`, `completed_at` | timestamptz | |

### `journal_entries`
| Column | Type | Rules |
|---|---|---|
| `id` | uuid PK | |
| `player_id` | uuid | |
| `title` | text | ≤ 120 chars |
| `detail` | text | ≤ 400 chars |
| `element` | text | |
| `occurred_at` | timestamptz | |
| | | After each insert, rows beyond the newest 100 for that player are deleted, oldest first (FR-021) |

### `reward_ledger` (idempotency, single source of truth for "at most once")
| Column | Type | Rules |
|---|---|---|
| `id` | bigserial | |
| `player_id` | uuid | |
| `kind` | text | RewardKind |
| `instance_key` | text | see the key table below |
| `request_id` | uuid | client retry key |
| `essence_delta`, `xp_delta` | int | |
| `result` | jsonb | the response returned on replays |
| `created_at` | timestamptz | |
| | | **unique (player_id, kind, instance_key)**; **unique (player_id, request_id)** |

| kind | instance_key | Guarantees |
|---|---|---|
| bootstrap | `bootstrap` | starter set granted once (R16) |
| discovery | `discovery:<request_id>` | a retried scan grants once; the daily cap of 20 is counted from the ledger |
| train | `train:<request_id>` | the cost is deducted exactly once (US2 scenario 1) |
| wave | `wave:<session_id>` | one reward per wave instance (FR-016, SC-004) |
| trail | `trail:<trail_id>:<local_date>` | once per trail per local date (FR-020) |

## 5. State transitions

**Battle session**

```text
start_trial ──► active ──(complete-trial: replay ends in victory)──► victory  [ledger wave:<id> → +60 essence, +100 XP]
                  │    └─(replay ends in defeat)──────────────────► defeat   [no reward, FR-017]
                  └──(newer session started / 24 h timeout)───────► abandoned [no reward]
```

A terminal session is immutable. Repeating `complete-trial` on it returns the stored result (R6).

**Discovery** (in the `discover` Edge Function, one transaction)

1. Validate the input.
2. Check the rate limit (30/hour).
3. Resolve the variant.
4. Compute familiarity against the player's encounters from the last 7 days (R8).
5. Insert the encounter.
6. Upsert the owned companion: new creature → L1, bond 15; already owned → +1 level, bond +15, capped at 100.
7. If under the daily cap, write ledger `discovery:<request_id>` (+15 essence, +50 XP).
8. Write the journal entry and prune the journal.

A below-threshold result never reaches the server: the client shows a soft fail (FR-003). If such a result does arrive, the server rejects it.

## 6. Derived values (pure functions, mirrored in Dart and TS)

| Function | Definition |
|---|---|
| `maxHp(creature, level)` | `baseHp + (level − 1) × 6` |
| `effectiveAttack(creature, level)` | `attack + (level − 1) × 2` |
| `playerLevel(xp)` | `floor(xp / 250) + 1` |
| `chooseVariant(family, attunement)` | the variant table in §2 |
| `familiarity(current, history)` | research R8 |
| `damage(...)`, `battleTurn(...)` | research R19 |
| `enemyTrio(wave)` | research R18 |
