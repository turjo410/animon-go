# Feature Specification: Cats-and-Dogs Identity Pilot

**Feature Branch**: `001-cats-dogs-identity-pilot`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Create a cats-and-dogs identity pilot. Testers can sign in, start guided capture, receive a matching decision, and view an existing animal record. An eligible verified animal can receive one exclusive collection claim. Another tester encountering that animal sees already collected. Uncertain, unfamiliar and failed results award nothing and can enter operator review. Record capture attempts, timing, outcomes and independent ground truth. Provide clearly labeled mock mode and a live mode. Export evaluation data."

**Traceability**: Seeded from [`docs/research/identity-pilot-setup-plan.md`](../../../docs/research/identity-pilot-setup-plan.md) and [`docs/research/animal-identification-rnd.md`](../../../docs/research/animal-identification-rnd.md); governed by [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) (this sub-project) and [`../../.specify/memory/constitution.md`](../../../.specify/memory/constitution.md) (main product, takes precedence on privacy/identity principles). Not part of the mobile MVP (`specs/001-mobile-core-loop` at the repo root) — this is a bounded research pilot whose outcome informs a later go/no-go decision.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guided capture and matching decision (Priority: P1)

A signed-in tester starts a guided capture of a cat or dog and receives a matching decision: a confident match to an existing registered animal (with its record shown), or a result indicating the animal is unfamiliar/uncertain/failed, with no claim made in that case.

**Why this priority**: This is the entire premise of the pilot — without a working, trustworthy capture-to-decision flow, there is nothing to evaluate.

**Independent Test**: Can be fully tested by running a capture in mock mode against a seeded set of known and unknown animal records and confirming the returned decision matches the seeded expectation — delivers the core evaluable behavior without requiring a live provider.

**Acceptance Scenarios**:

1. **Given** a signed-in tester, **When** they start guided capture of a previously-registered animal, **Then** they receive a confident match decision and can view that animal's existing record.
2. **Given** a signed-in tester, **When** they capture an animal that has no registered record, **Then** they receive an "unfamiliar" decision and no record is created automatically.
3. **Given** a capture that the provider cannot confidently resolve either way, **When** the decision is returned, **Then** it is shown as "uncertain," not forced into either a match or no-match outcome.
4. **Given** any decision returned to the tester, **When** it is displayed or stored, **Then** it is unambiguously labeled as having come from mock mode or live mode — never ambiguous between the two.

---

### User Story 2 - Exclusive claim and duplicate protection (Priority: P1)

An eligible, confidently-verified animal can be claimed into one tester's collection exactly once; a second tester who later encounters the same real animal sees that it is already collected rather than being able to claim it again.

**Why this priority**: This is the specific risk the pilot exists to de-risk for the main product — without provable exclusivity, "collection" has no integrity and the whole mechanic is untrustworthy.

**Independent Test**: Can be fully tested with two test accounts both attempting to claim the same seeded animal record (including a simulated near-simultaneous attempt) and confirming exactly one claim succeeds — delivers the exclusivity guarantee independently of real capture hardware.

**Acceptance Scenarios**:

1. **Given** a confidently-matched, previously-unclaimed animal, **When** the tester accepts the result, **Then** that animal becomes claimed by that tester and no other tester can claim it afterward.
2. **Given** an animal that is already claimed, **When** a different tester encounters and confidently matches that same animal, **Then** they see it as "already collected" and are not offered a claim.
3. **Given** two claim attempts on the same previously-unclaimed animal arriving at effectively the same time, **When** both are processed, **Then** exactly one succeeds and the other is rejected as already-claimed — never both, never neither.

---

### User Story 3 - Evaluation data and operator review (Priority: P2)

Every capture attempt — matched, unfamiliar, uncertain, or failed — is recorded with its timing and outcome, uncertain or borderline results can be routed to an operator for review, and the accumulated evaluation data can be exported for analysis against independently known ground truth.

**Why this priority**: The pilot's purpose is to produce a decision-grade evaluation, not just a working demo; this story is what turns captures into evidence. It builds on User Stories 1–2 but is not required for a single capture-and-claim flow to work.

**Independent Test**: Can be fully tested by running a batch of seeded capture attempts (including deliberately uncertain and failed ones) and confirming every attempt appears in an exported dataset with its outcome and timing, and that uncertain attempts appear in an operator review queue — delivers evaluation value independently of the live provider being connected.

**Acceptance Scenarios**:

1. **Given** any capture attempt (successful, unfamiliar, uncertain, or failed), **When** it completes, **Then** a record is stored with its outcome, timestamp, and elapsed time, regardless of whether it resulted in a match.
2. **Given** an uncertain or borderline result, **When** it is produced, **Then** it is placed into an operator review queue rather than being silently resolved either way.
3. **Given** an operator reviewing a queued result, **When** they make a determination, **Then** that determination is recorded and does not retroactively change already-stored capture-attempt records, only the resulting state going forward.
4. **Given** an accumulated set of capture-attempt records, **When** an authorized user requests an evaluation export, **Then** a dataset is produced containing outcomes, timings, and mock/live labels suitable for comparison against independently-tracked ground truth.

---

### Edge Cases

- What happens when a tester's capture fails before reaching the provider (e.g., bad image, aborted session)? It is recorded as a failed attempt with a reason, not silently dropped — all capture attempts count toward evaluation per the pilot's constitution.
- What happens when the live provider is temporarily unavailable? The attempt is recorded as failed/errored (clearly distinguished from "unfamiliar"), and the tester is not told an animal is unfamiliar when the real cause is a provider outage.
- What happens when an operator mistakenly confirms an uncertain result as a match to the wrong existing record? This spec requires the determination to be recorded and auditable (who, when, what was decided) so such an error is traceable; correcting it is an operational process, not an automatic system behavior.
- What happens if the same tester attempts to re-register or re-claim an animal they already own? The system recognizes the existing claim and does not create a duplicate record or duplicate claim for the same tester.
- How is a mock-mode capture prevented from being exported or treated as live evidence? Every stored record and every export carries an explicit mock/live label; evaluation analysis must be able to filter by it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require testers to sign in before starting a guided capture.
- **FR-002**: The system MUST provide a guided capture flow for cats and dogs that produces one of: confident match, unfamiliar, uncertain, or failed.
- **FR-003**: The system MUST NOT create a new animal record or award a claim automatically on an uncertain, unfamiliar, or failed result.
- **FR-004**: The system MUST verify every match result server-side before it can affect collection state; a client-only or redirect-only result MUST NOT be trusted.
- **FR-005**: The system MUST let a tester view the existing record of an animal they have confidently matched.
- **FR-006**: The system MUST allow at most one active collection claim per verified animal identity, enforced such that two concurrent claim attempts on the same unclaimed animal cannot both succeed.
- **FR-007**: The system MUST show a tester who encounters an already-claimed animal an "already collected" result rather than an option to claim it.
- **FR-008**: The system MUST provide a mock provider mode that requires no external network dependency and a live provider mode (self-hosted: a frozen pretrained embedding extractor plus our own similarity matching), with every stored result and every display explicitly labeled as mock or live.
- **FR-009**: The system MUST record every capture attempt — including failed and uncertain ones — with its outcome and elapsed time.
- **FR-010**: The system MUST route uncertain results into an operator review queue.
- **FR-011**: The system MUST allow an authorized operator to record a review determination for a queued result, with that determination itself recorded (who, when, what was decided).
- **FR-012**: The system MUST support exporting accumulated evaluation data (outcomes, timings, mock/live labels) for comparison against independently-tracked ground truth.
- **FR-013**: The system MUST exclude participant data, real capture evidence, and ground-truth identity records from version control, consistent with this pilot's constitution.
- **FR-014**: The system MUST NOT present any result as biometric certainty; results are framed as matching decisions with an associated confidence/outcome category, not identity proof.

### Key Entities

- **Tester**: A signed-in pilot participant who performs captures and may hold collection claims.
- **Operator**: An authorized reviewer who resolves queued uncertain results; distinct from a Tester.
- **Animal Identity**: A shared record representing one real, registered cat or dog, independent of which tester(s) have encountered it.
- **Capture Attempt**: One guided-capture event: tester, timestamp, elapsed time, outcome (match / unfamiliar / uncertain / failed), and mock-or-live label.
- **Collection Claim**: The record of which tester (if any) currently holds the exclusive claim on a given Animal Identity.
- **Review Determination**: An operator's recorded resolution of a queued uncertain Capture Attempt.
- **Evaluation Export**: A generated dataset of Capture Attempts and their outcomes, suitable for comparison against independently-tracked ground truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of capture attempts in a test run (matched, unfamiliar, uncertain, and failed) appear in the evaluation export with a recorded outcome and elapsed time — none are silently dropped.
- **SC-002**: Zero instances, across concurrent-claim testing, of the same Animal Identity ending up with more than one active Collection Claim.
- **SC-003**: 100% of stored results and displayed decisions carry an explicit, correct mock-or-live label in testing across both modes.
- **SC-004**: 100% of uncertain results in a test run are present in the operator review queue, with zero uncertain results auto-resolved into either a match or a new-animal outcome.
- **SC-005**: The pilot can run a 30-animal evaluation batch (15 cats, 15 dogs, split between registered and held-out unfamiliar animals, per `docs/research/identity-pilot-setup-plan.md` §7) entirely in mock mode with no external credentials required.

## Assumptions

- "Guided capture" means a capture flow we design ourselves (framing guidance, basic anti-spoof/liveness checks) to produce a consistent, comparable photo for the self-hosted embedding extractor; since there is no vendor-prescribed flow, its exact UI is a planning-level decision, not fixed by this spec.
- Mock mode is deterministic and seedable for testing (e.g., can be configured to return a specific outcome for a given test input), so that User Stories 1–3 are independently testable without live provider access.
- "Eligible" animal, for claim purposes, means a confidently-matched, previously-unclaimed Animal Identity; eligibility criteria beyond that (e.g., minimum enrollment evidence, calibrated similarity threshold) are a planning-level detail informed by this pilot's own calibration evaluation.
- Species scope for this pilot is cats and dogs only; birds, insects, and any other species are explicitly out of scope, per `docs/research/animal-identification-rnd.md`.
- This pilot does not itself integrate with the mobile product (`apps/mobile`); it is a standalone evaluation whose results inform a later, separate integration decision (`docs/ROADMAP.md` Phase 2/3).
