# shared/game-vectors

Golden test cases for Animon GO's game rules. They're consumed by **both**:

- the Dart engine (client): `apps/mobile/test/core/game/*_test.dart`
- the TypeScript engine (server replay): `supabase/functions/_shared/vectors.test.ts`

Each file is a JSON array of `{ "name", "input", "expected" }`. The full format is in [`specs/001-mobile-core-loop/contracts/game-rules-vectors.md`](../../specs/001-mobile-core-loop/contracts/game-rules-vectors.md).

**Change rule:** changing any game constant or formula means updating these vectors in the **same** change. Both test suites must pass before merge.

The expected values are generated from the ported prototype formulas (`animon-web/src/lib/game.ts`, read-only reference) by `shared/game-vectors/generate.mjs`.
