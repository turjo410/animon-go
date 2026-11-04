# Animal identity pilot setup plan

**Prepared:** 4 November 2026  
**Purpose:** organize a small pilot with GitHub Spec Kit, then test individual animal identification without training a model.  
**Status:** proposed setup and implementation plan; initialization has not been executed.

## 1. Define the first pilot

Build one complete experiment: **capture a cat or dog, search existing identities, and determine whether that individual already has a collection claim.** Start with Petify as the live provider and a clearly labeled mock provider for development.

The pilot should answer three questions:

- Can people complete the required capture during a realistic encounter?
- Can the service recognize a registered animal across different people, phones and days, while rejecting unfamiliar animals?
- Can two players encounter the same animal without receiving separate exclusive claims?

Birds and insects remain research extensions. Supporting them must require evidence for those species. Defer custom model training, maps, AR and combat implementation until the identity experiment produces a useful result.

## 2. Initialize a separate project

Use this proposed location:

```text
/Users/turjokhan/Developer/Animon Go/animon-identity-pilot/
```

Initialize Spec Kit inside this new project. The parent directory contains several projects and is not currently a Git repository. Give the pilot its own repository and dependency lockfile.

`uv`, Git, Node.js and pnpm are available in this environment. The `specify` executable was not found. Spec Kit currently requires Python 3.11+; verify the runtime before installation. Its current Codex setup uses `--integration codex` and installs skills under `.agents/skills/`. [Installation guide](https://github.github.com/spec-kit/installation.html), [Codex integration](https://github.github.com/spec-kit/integrations/codex.html)

Proposed terminal sequence:

```sh
cd '/Users/turjokhan/Developer/Animon Go'
uv tool install specify-cli
specify version
specify init animon-identity-pilot --integration codex --script sh --non-interactive
cd animon-identity-pilot
```

Record the installed Spec Kit version in `docs/toolchain.md`, verify the generated skills and ensure the pilot root has its own Git repository. If it does not, run `git init` there. Use the official initializer to generate Spec Kit files; do not substitute hand-written placeholder skills. Open the pilot directory as the working project before invoking its skills.

## 3. Keep the toolchain small

| Need | Proposed choice | Reason |
| --- | --- | --- |
| Capture launcher, results and server endpoints | TypeScript + Next.js | One application for the experiment interface and provider integration. [Route handlers](https://nextjs.org/docs/app/getting-started/route-handlers) |
| Individual recognition | Petify hosted capture and server API | Avoids model training and native camera integration during the first experiment. Use server-verified results for collection decisions. [Integration guide](https://docs.petnow.io/petify/docs/server/web-integration/intro) |
| Accounts and shared records | Supabase Auth + PostgreSQL | Identifiable testers, shared animal identities and transaction-based claim enforcement. [Database documentation](https://supabase.com/docs/guides/database/overview) |
| Verification | Vitest + Playwright + PostgreSQL integration tests | Check decision rules, retries, authorization, concurrent claims and the capture handoff. [Vitest](https://vitest.dev/guide/), [Playwright](https://playwright.dev/docs/intro) |
| Repeatable development | pnpm lockfile, linting, type checking and CI | Make the same checks reproducible locally and in CI. |

No GPU or vector database is needed for this provider-backed pilot. Pin compatible runtime and package versions when scaffolding.

## 4. Planned directory layout

This is the target layout after initialization and feature planning. Let Spec Kit create its managed directories and feature names.

```text
animon-identity-pilot/
  .agents/skills/             # Generated Spec Kit skills
  .specify/                  # Generated templates, scripts and constitution
  specs/<pilot-feature>/
    spec.md                  # User stories and acceptance criteria
    plan.md                  # Technical design
    research.md              # Verified provider behavior and unresolved questions
    data-model.md
    contracts/               # Application and provider boundaries
    quickstart.md
    tasks.md
  src/
    app/                     # Capture launcher, callback, results and review
    lib/providers/           # Mock provider and Petify adapter
    lib/identity/            # Matching decisions and enrollment review
    lib/claims/              # Exclusive collection rules
  supabase/migrations/
  tests/                     # Unit, integration and browser checks
  docs/
    research.md
    pilot-protocol.md
    pilot-results.md
    decisions/
    toolchain.md
  data/private/              # Local participant and evaluation data, ignored by Git
  .env.example
  .gitignore
  AGENTS.md
  README.md
```

`AGENTS.md` should describe the project, commands, provider boundary and evidence requirements. `.env.example` should document variable names with empty values. Exclude credentials, real capture data and participant records from Git. Keep provider server keys server-side and store only the evidence required for the experiment.

## 5. Run the Spec Kit workflow

Use these as chat prompts after initialization, one at a time. The current Codex integration uses `$speckit-...` skills. These are agent prompts, not terminal commands. [Workflow reference](https://github.github.com/spec-kit/quickstart.html)

### Establish project principles

```text
$speckit-constitution
Create principles for an animal identity pilot: no custom model training;
provider results must be verified server-side; mock and live evidence must
be distinguishable; uncertain or unmatched scans never automatically award
a new animal; each verified animal has one shared identity and at most one
active collection claim; all capture failures count in evaluation; keep
participant data private; prefer a small, reproducible implementation.
```

### Specify the experiment

```text
$speckit-specify
Create a cats-and-dogs identity pilot. Testers can sign in, start guided
capture, receive a matching decision, and view an existing animal record.
An eligible verified animal can receive one exclusive collection claim.
Another tester encountering that animal sees already collected. Uncertain,
unfamiliar and failed results award nothing and can enter operator review.
Record capture attempts, timing, outcomes and independent ground truth.
Provide clearly labeled mock mode and a live mode. Export evaluation data.
```

Next run `$speckit-clarify`, focusing on eligibility for new enrollment, match thresholds, provider permissions, capture practicality, data retention and pilot success criteria. Record unresolved provider facts as blockers for the dependent live feature.

### Plan implementation

```text
$speckit-plan
Use TypeScript, Next.js, pnpm, Supabase Auth and PostgreSQL. Define a provider
adapter with mock and Petify implementations. Start with mock mode, then
integrate hosted live capture through server-issued sessions. Verify results
server-side and make repeated callbacks safe. Use migrations and a database
constraint for one active claim per animal. Provide operator-reviewed new
enrollment and duplicate resolution. Add meaningful automated checks and a
30-animal evaluation protocol. No model training or native camera SDK yet.
```

Then run `$speckit-checklist`, `$speckit-tasks` and `$speckit-analyze`. Resolve material gaps before `$speckit-implement`. Work through the phases below; use `$speckit-converge` to identify remaining work against the specification. Keep generated checklists accurate—passing a specification review is not evidence that the software or identification model works.

## 6. Build in this order

| Phase | Deliverable | Completion checkpoint |
| --- | --- | --- |
| 1. Foundation | Spec Kit artifacts, project scaffold, configuration, accounts and CI | A fresh checkout can run documented checks; credentials are unnecessary for mock mode. |
| 2. Mock workflow | Capture handoff, result states, review queue and claim handling | Repeat requests are safe; two concurrent claims for the same animal cannot both succeed; mock results are labeled. |
| 3. Provider feasibility | A few guided captures on real phones | Record whether the capture process fits intended encounters before expanding integration. |
| 4. Live integration | Server-issued sessions, trusted result retrieval and stable identity mapping | Validate against current provider documentation; handle expiry, failures and retries; never trust a browser redirect alone. |
| 5. Field evaluation | Recorded real-animal attempts and a result sheet | Compare repeat matches, unfamiliar-animal handling, failure rates, capture time and cost. |
| 6. Decision | Proceed, investigate another provider, or revise scope | State the evidence and remaining limitations; do not infer universal animal coverage. |

## 7. Write the evaluation protocol before collecting results

Suggested initial sample: **30 animals—15 cats and 15 dogs.** Register 10 of each and hold out five of each as unfamiliar animals. Use separate capture sessions across two operators, two phones and different days. Include similar-looking animals and more than one tester account for the same animal. Keep ground-truth identities separate from provider predictions.

Report registered-animal recognition, wrong matches, unfamiliar animals incorrectly accepted, uncertain results, incomplete captures and end-to-end time. Break results down by animal group and phone. Track repeated enrollment attempts as well as concurrent claims: one database constraint cannot detect an animal mistakenly assigned two different identities.

Agree on provisional success criteria before the trial. Any wrong-animal award should block expansion until understood. A small pilot with no observed errors is only preliminary evidence and must lead to larger testing before public use.

## 8. Inputs needed for live testing

- Petify account with identification access, server credentials and a configured return URL; confirm current trial and billing terms.
- A test Supabase project and an HTTPS-accessible deployment for phone-based testing.
- Consenting participants, known animals and two phones.
- A named operator for reviewing uncertain matches and new enrollment.

Development can start in mock mode while these inputs are arranged. Real identity accuracy, capture suitability and cost remain unverified until the live trial.

**Immediate next action:** initialize `animon-identity-pilot`, generate the constitution and first feature specification, and review their acceptance criteria before generating the implementation tasks.
