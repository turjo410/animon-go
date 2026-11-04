# AGENTS.md — working conventions for this repository

This file governs how an AI coding agent (or a human) should operate in this monorepo. It is deliberately short; the reasoning lives in `docs/`.

## Hard boundaries

- **Never read, edit, or reference `twntis-film/`.** It is a separate, unrelated project. It is excluded from this repo's `.gitignore` on purpose.
- **Treat `animon-web/` as read-only.** It is a different git repository (its own `.git/`) and the validated reference prototype for game design. Port ideas from it into `apps/mobile`; do not edit it from here, and do not assume its code is the production implementation.
- **The real product is `apps/mobile` (Flutter, iOS + Android).** Not a web app. `animon-web` proved the game loop; it is not what ships.
- **`animon-identity-pilot/` is a bounded experiment**, not a product feature yet. It must stay clearly labeled mock-vs-live in everything it produces, per `docs/SRS.md` §4.4 and §6.

## Where things live

| Question | Answer |
|---|---|
| Why are we building this? | `docs/BRD.md` |
| What should it do? | `docs/PRD.md` |
| What are the system requirements? | `docs/SRS.md` |
| How is it structured? | `docs/ARCHITECTURE.md` |
| What order are we building it in? | `docs/ROADMAP.md` |
| Prior research (animal ID, pilot plan) | `docs/research/` |
| Significant decisions and why | `docs/decisions/` |

## Process

Feature work goes through Spec Kit, not ad hoc implementation:

1. `/speckit-constitution` — once, to establish principles (already drafted conceptually in `docs/BRD.md`/`docs/SRS.md`; Spec Kit's generated constitution should be consistent with them, not contradict them).
2. `/speckit-specify` — one feature at a time, user-facing behavior.
3. `/speckit-clarify` — resolve ambiguity before planning.
4. `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.

Keep `docs/BRD.md`, `docs/PRD.md`, and `docs/SRS.md` as the stable baseline. If a Spec Kit feature spec needs to contradict them, update the baseline deliberately (and note it in `docs/decisions/`) rather than letting them drift silently out of sync.

## Code conventions

- Flutter app (`apps/mobile`): feature-first folders under `lib/features/`, shared code under `lib/core/` and `lib/data/`. See each folder's `README.md` for intended contents before adding files.
- Don't add a new top-level stack choice (another backend, another mobile framework) without a decision record in `docs/decisions/` — see `docs/ARCHITECTURE.md` §7 for the format and existing entries.
- No secrets committed. `.env` files are git-ignored; document required variables in `.env.example` files per sub-project.
