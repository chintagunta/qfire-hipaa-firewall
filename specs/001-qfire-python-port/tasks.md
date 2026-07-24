---

description: "Task list for QFIRE Python Port"
---

# Tasks: QFIRE Python Port

**Input**: Design documents from `/specs/001-qfire-python-port/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md, quickstart.md

**Tests**: Included — constitution Principle III (Test-First, NON-NEGOTIABLE) and spec FR-006
require exemplar-driven tests; test tasks below MUST be written and observed failing before
their paired implementation task.

**Organization**: Tasks are grouped by user story (spec.md priorities) to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US4)
- File paths are exact, per plan.md's Project Structure section

## Path Conventions

Single-project library layout per plan.md: `src/qfire/`, `tests/`, `rules/`, `chains/` at
repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Add dependencies (`PyYAML`, `regex`, `onnxruntime`, `tokenizers`) and dev dependency
      (`pytest`) to `pyproject.toml` per research.md's dependency footprint table
- [X] T002 [P] Create package skeleton: `src/qfire/__init__.py`, `src/qfire/nodes/__init__.py`
      (empty modules with docstrings only, per plan.md Project Structure)
- [X] T003 [P] Create test/data directories: `tests/unit/`, `tests/integration/`,
      `tests/rules/`, `tests/fixtures/broken_rules/`, `tests/fixtures/broken_chains/`,
      `rules/injection/`, `rules/healthcare/`, `chains/`

**Checkpoint**: Package importable (`import qfire`), directories exist for all later tasks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core rule/chain/trace infrastructure that every user story's evaluation depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement error types `QfireError`, `RuleValidationError`, `ChainValidationError`
      (with `.file`/`.field` attributes) in `src/qfire/errors.py` per contracts/public-api.md
- [X] T005 [P] Implement `Rule` and `ExemplarSet` dataclasses plus `load_rules(path)` YAML
      loader/validator in `src/qfire/rules.py` per data-model.md's Rule/ExemplarSet tables
      (depends on T004)
- [X] T006 [P] Implement `DetectorNode` base contract (type/config fields, runtime verdict
      shape: verdict/confidence/rationale/latency_ms) in `src/qfire/nodes/__init__.py` per
      data-model.md's DetectorNode section (depends on T004)
- [X] T007 Implement `Chain` dataclass plus `load_chains(path, rules)` YAML loader/validator
      (ordered + expression mode schemas, rule-id reference resolution) in
      `src/qfire/chains.py` per data-model.md's Chain table (depends on T004, T005)
- [X] T008 [P] Implement `DecisionTrace` and `NodeResult` dataclasses plus a JSON-lines
      append-only audit log writer in `src/qfire/trace.py` per data-model.md's DecisionTrace
      section and constitution Principle V (depends on T004)
- [X] T009 Implement chain evaluation engine: ordered-mode execution with cheapest-first
      short-circuit and fail-closed error handling, writing a DecisionTrace per evaluation, in
      `src/qfire/chains.py` (depends on T006, T007, T008)
- [X] T010 Implement expression-mode (boolean DAG over rule ids/groups) evaluation in
      `src/qfire/chains.py` (depends on T009)

**Checkpoint**: Foundation ready — rule/chain loading, the DetectorNode contract, and both
chain evaluation modes work end-to-end with a stub node type; user story implementation can
now begin.

---

## Phase 3: User Story 1 - Evaluate a prompt and get an allow/block decision (Priority: P1) 🎯 MVP

**Goal**: A developer can load a chain and get a correct, explainable allow/block decision for
any prompt, with expensive pipeline nodes skipped once a cheaper node already decides.

**Independent Test**: Load a chain with one injection-detection rule; submit a benign and a
malicious prompt; confirm benign → allow, malicious → block with the firing rule identified.

### Tests for User Story 1 ⚠️

> Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for the pattern/lexical detector node (deny-list match →
      block, no match → abstain) in `tests/unit/test_pattern_node.py`
- [X] T012 [P] [US1] Integration test: benign prompt → allow, malicious prompt → block with
      `fired_rule_id` populated, via `evaluate()` in `tests/integration/test_evaluate_basic.py`
      (spec Story 1 acceptance scenarios 1-2)
- [X] T013 [P] [US1] Integration test: a rule with a cheap node that blocks first confirms the
      pipeline's remaining (simulated expensive) node never runs, in
      `tests/integration/test_short_circuit.py` (spec Story 1 acceptance scenario 3)

### Implementation for User Story 1

- [X] T014 [US1] Implement the pattern/lexical detector node (`regex` module primary, stdlib
      `re` fallback) in `src/qfire/nodes/pattern.py` (depends on T006; makes T011 pass)
- [X] T015 [US1] Implement public `evaluate(prompt, chain_id, chains, *, normalize=True)` in
      `src/qfire/__init__.py`, wiring rule/chain loading, the evaluation engine, and trace
      logging per contracts/public-api.md (depends on T009, T010, T014; makes T012-T013 pass)
- [X] T016 [US1] Author sample injection-detection rule and ordered chain YAML in
      `rules/injection/injection_defense.yaml` and `chains/injection_ordered.yaml`, matching
      the reference format referenced in research.md and spec Assumptions

**Checkpoint**: User Story 1 fully functional and independently testable — `evaluate()` gives
correct, explainable, short-circuited decisions using pattern-based rules.

---

## Phase 4: User Story 2 - Author and validate rules as declarative data (Priority: P1)

**Goal**: A policy author can write a rule's scope, pipeline, and exemplars in YAML and get a
pass/fail validation report against those exemplars, plus a clear error on a malformed file.

**Independent Test**: Author a rule file with one in-scope and one out-of-scope example; run
validation; confirm both report the expected verdict. Author a rule file missing a required
field; confirm a clear file+field error.

### Tests for User Story 2 ⚠️

- [X] T017 [P] [US2] Unit test `validate_rule()` reports pass/fail per exemplar against
      expected verdict in `tests/unit/test_validate_rule.py` (spec Story 2 acceptance scenario 1)
- [X] T018 [P] [US2] Unit test loading a rule file with a missing/malformed required field
      raises `RuleValidationError` naming the file and field in
      `tests/unit/test_rule_validation_errors.py` (spec Story 2 acceptance scenario 2)

### Implementation for User Story 2

- [X] T019 [US2] Implement `validate_rule(rule) -> ExemplarValidationResult` in
      `src/qfire/rules.py`, evaluating each exemplar against the rule alone per
      contracts/public-api.md (depends on T005, T009; makes T017 pass)
- [X] T020 [US2] Harden `load_rules()`'s field validation to cover every required field per
      data-model.md's Rule validation rules, with file+field detail in the raised error
      (depends on T005; makes T018 pass)
- [X] T021 [US2] Add exemplar-driven parametrized test generator
      `tests/rules/test_exemplars.py` that loads every rule under `rules/` and asserts each
      exemplar matches its expected verdict (constitution Principle III enforcement mechanism)

**Checkpoint**: User Stories 1 AND 2 both work independently — rules can be authored, tested
via their own exemplars, and evaluated in a chain.

---

## Phase 5: User Story 3 - Detect and flag protected health information (Priority: P2)

**Goal**: A prompt containing a synthetic protected-health identifier is flagged with its
category, independent of whether any injection rule also fires.

**Independent Test**: Submit a prompt containing a synthetic medical-record-number pattern;
confirm a PHI category match is reported. Submit a clean prompt; confirm no match.

### Tests for User Story 3 ⚠️

- [X] T022 [US3] Unit tests for the PHI detector node: synthetic identifier → match with
      correct category, clean prompt → no match, in `tests/unit/test_phi_node.py` (spec Story
      3 acceptance scenarios 1-2)

### Implementation for User Story 3

- [X] T023 [US3] Implement the PHI detector node covering the 18-identifier HIPAA safe-harbor
      panel in `src/qfire/nodes/phi.py` per data-model.md's Identifier Panel section (depends
      on T006; makes T022 pass)
- [X] T024 [P] [US3] Author sample healthcare rule and chain YAML in
      `rules/healthcare/phi_panel.yaml` and `chains/hipaa_phi.yaml`
- [X] T025 [US3] Integration test confirming a PHI match is reported via `evaluate()`
      regardless of injection-rule outcome, in `tests/integration/test_phi_evaluate.py`
      (depends on T015, T023, T024)

**Checkpoint**: User Stories 1, 2, AND 3 all work independently — PHI detection composes with
the core evaluation engine.

---

## Phase 6: User Story 4 - Recover obfuscated payloads before detection (Priority: P3)

**Goal**: An attack instruction hidden via Base64/hex/ROT13/homoglyph/leetspeak/zero-width
encoding is caught by the same rule that catches its plain-text equivalent, only when
normalization is enabled.

**Independent Test**: Submit a Base64-encoded attack instruction with normalization on
(caught) and off (missed), comparing against the plain-text equivalent (always caught).

### Tests for User Story 4 ⚠️

- [X] T026 [P] [US4] Unit tests for the normalization pass covering Base64, hex, ROT13,
      homoglyph, leetspeak, and zero-width-character recovery in `tests/unit/test_normalize.py`

### Implementation for User Story 4

- [X] T027 [US4] Implement the de-obfuscation normalization pass in `src/qfire/normalize.py`
      (depends on T006; makes T026 pass)
- [X] T028 [US4] Wire `normalize` flag in `evaluate()` to run detection against the
      normalized view of the prompt in addition to the raw view in `src/qfire/__init__.py`
      (depends on T015, T027)
- [X] T029 [US4] Integration test: encoded attack caught with `normalize=True`, missed with
      `normalize=False`, plain-text equivalent always caught, in
      `tests/integration/test_normalize_evaluate.py` (spec Story 4 acceptance scenarios 1-2)

**Checkpoint**: All four user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Remaining FR-005 detector node types not tied to a single user story, plus
fail-closed hardening and documentation

- [X] T030 [P] Implement the local injection classifier node (`onnxruntime` CPU execution
      provider + `tokenizers`) in `src/qfire/nodes/classifier.py`, with a documented,
      explicitly-reported degraded lexical-only fallback when no ONNX model is present per
      research.md
- [X] T031 [P] Implement the LLM scope-judge node (`urllib.request`, JSON POST with timeout)
      in `src/qfire/nodes/judge.py`
- [X] T032 [P] Unit tests for the classifier node, including the degraded-fallback path, in
      `tests/unit/test_classifier_node.py` (depends on T030)
- [X] T033 [P] Unit tests for the judge node (including a timeout/error → abstain-or-fail-closed
      case) in `tests/unit/test_judge_node.py` (depends on T031)
- [X] T034 Fail-closed edge-case integration test: a rule with a deliberately broken detector
      node produces `decision == "block"` with `trace.error` populated, in
      `tests/integration/test_fail_closed.py`, using fixtures in
      `tests/fixtures/broken_rules/` and `tests/fixtures/broken_chains/` (spec edge case,
      FR-010, constitution Principle V)
- [X] T035 [P] Write `README.md` usage section matching quickstart.md's examples
- [X] T036 Run all quickstart.md validation scenarios manually and confirm expected output for
      each

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 (both P1) can proceed in parallel after Foundational
  - US3 (P2) depends only on Foundational + the DetectorNode contract (T006); does not require
    US1/US2 code but its integration test (T025) uses `evaluate()` from US1 (T015)
  - US4 (P3) depends only on Foundational; its integration test (T029) likewise uses
    `evaluate()` from US1 (T015)
- **Polish (Phase 7)**: Classifier/judge nodes (T030-T033) depend only on Foundational (T006)
  and can start any time after Phase 2; T034/T036 depend on all prior phases

### User Story Dependencies

- **User Story 1 (P1)**: Foundational only
- **User Story 2 (P1)**: Foundational only (independently testable via `validate_rule()`
  without needing full chain evaluation, though T021 benefits from US1's sample rules)
- **User Story 3 (P2)**: Foundational + DetectorNode contract; integration test uses US1's
  `evaluate()` but PHI detection logic itself (T023) has no US1/US2 dependency
- **User Story 4 (P3)**: Foundational + DetectorNode contract; integration test uses US1's
  `evaluate()` but normalization logic itself (T027) has no US1/US2/US3 dependency

### Within Each User Story

- Tests written and observed failing before implementation (constitution Principle III)
- Detector node implementation before the integration test that exercises it through
  `evaluate()`
- Story complete before moving to the next priority (though stories are independent enough to
  parallelize across contributors)

### Parallel Opportunities

- T002, T003 (Setup) in parallel
- T005, T006, T008 (Foundational) in parallel after T004
- Once Foundational (Phase 2) completes: US1, US2, US3's detector work (T023), and US4's
  normalization work (T027) can all start in parallel
- T011, T012, T013 (US1 tests) in parallel
- T017, T018 (US2 tests) in parallel
- T024 (US3 sample YAML) in parallel with T023 (US3 detector)
- T026 (US4 test) in parallel with nothing else in US4 until T027 lands (single-file sequence
  T027 → T028 → T029)
- T030, T031, T032, T033, T035 (Polish) in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test pattern node in tests/unit/test_pattern_node.py"
Task: "Integration test benign/malicious via evaluate() in tests/integration/test_evaluate_basic.py"
Task: "Integration test short-circuit in tests/integration/test_short_circuit.py"
```

## Parallel Example: Foundational Phase

```bash
# After T004 (errors.py) lands, launch together:
Task: "Rule/ExemplarSet dataclasses + load_rules() in src/qfire/rules.py"
Task: "DetectorNode base contract in src/qfire/nodes/__init__.py"
Task: "DecisionTrace/NodeResult + audit log writer in src/qfire/trace.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run `tests/integration/test_evaluate_basic.py` and the relevant
   quickstart.md scenario independently
5. Demo: `evaluate()` correctly allows/blocks using a pattern-based injection rule

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add US1 → test independently → MVP demo
3. Add US2 → test independently → policy authors can now write/validate their own rules
4. Add US3 → test independently → healthcare PHI panel available
5. Add US4 → test independently → de-obfuscation hardens all prior rules against evasion
6. Polish phase → classifier/judge node types, fail-closed hardening, docs

### Parallel Team Strategy

With multiple developers, after Foundational is done:

- Developer A: User Story 1 (T011-T016)
- Developer B: User Story 2 (T017-T021)
- Developer C: User Story 3 (T022-T025) + classifier node (T030, T032)
- Developer D: User Story 4 (T026-T029) + judge node (T031, T033)

---

## Notes

- [P] tasks touch different files with no unmet dependencies
- [Story] label maps each task to its user story for traceability
- Every story is independently completable and testable per its Independent Test statement
- Tests must be written and observed failing before their paired implementation task
  (constitution Principle III, NON-NEGOTIABLE)
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- Classifier (T030) and judge (T031) nodes are shared FR-005 capabilities, not tied to a
  single user story per spec.md, so they live in Polish rather than blocking any story's
  checkpoint
