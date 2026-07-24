# Feature Specification: QFIRE Python Port

**Feature Branch**: `001-qfire-python-port`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "build an efficient python library that is a port of the qfire library"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate a prompt against a declared scope and get an allow/block decision (Priority: P1)

A developer integrating an LLM agent into their application wants every prompt reaching the
model checked against a set of rules before it is forwarded, so that out-of-scope requests
and known attack patterns are stopped before the model ever sees them.

**Why this priority**: This is the core value proposition of the firewall — without a working
allow/block decision, nothing else in the library matters.

**Independent Test**: Can be fully tested by loading a rule/chain definition, submitting a
benign prompt and a malicious prompt, and confirming the benign one is allowed and the
malicious one is blocked with a reason.

**Acceptance Scenarios**:

1. **Given** a chain with one injection-detection rule, **When** a prompt containing a known
   jailbreak pattern is evaluated, **Then** the decision is "block" and includes which rule fired.
2. **Given** the same chain, **When** an ordinary benign prompt is evaluated, **Then** the
   decision is "allow".
3. **Given** a rule pipeline with multiple detector nodes, **When** the cheapest node already
   determines a block, **Then** the remaining, more expensive nodes are not executed.

---

### User Story 2 - Author and validate rules as declarative data (Priority: P1)

A policy author (not necessarily a programmer) wants to define a rule's scope, detector
pipeline, and example prompts in a structured file, and have the library validate that the
rule behaves as intended against its own examples.

**Why this priority**: Declarative, testable policy is what distinguishes this firewall from a
hard-coded filter; it must be usable on day one alongside the evaluation engine.

**Independent Test**: Can be fully tested by authoring a rule file with in-scope and
out-of-scope example prompts and running a validation command that reports pass/fail per
example without writing any Python code.

**Acceptance Scenarios**:

1. **Given** a rule file with an in-scope and an out-of-scope example, **When** the rule is
   validated, **Then** the library reports whether each example produced the expected verdict.
2. **Given** a rule file with a malformed or missing required field, **When** it is loaded,
   **Then** the library reports a clear validation error identifying the file and field.

---

### User Story 3 - Detect and flag protected health information in a prompt (Priority: P2)

An integrator building a healthcare-adjacent agent wants prompts scanned for the standard
set of protected health information identifiers, so that requests attempting to exfiltrate or
expose patient data are caught even when they carry no obvious attack signal.

**Why this priority**: This is the differentiating capability for regulated domains, but the
library must first work as a general-purpose firewall (Story 1) before this specialized panel
is meaningful.

**Independent Test**: Can be fully tested by submitting a prompt containing a synthetic patient
identifier (e.g., a medical record number) and confirming it is flagged with the matching
identifier category, independent of whether any injection rule fires.

**Acceptance Scenarios**:

1. **Given** the standard protected-identifier panel is enabled, **When** a prompt contains a
   synthetic identifier from that panel, **Then** the decision reports a match with its category.
2. **Given** the same panel, **When** a prompt contains no such identifiers, **Then** no
   identifier match is reported.

---

### User Story 4 - Recover obfuscated payloads before detection (Priority: P3)

A security-conscious integrator wants prompts that hide instructions using encoding tricks
(Base64, hex, ROT13, homoglyphs, leetspeak, zero-width characters) to be normalized before
detection runs, so that obfuscation cannot bypass otherwise-effective rules.

**Why this priority**: This hardens detection against a known evasion class but is only
valuable once the core evaluation and rule authoring flows (Stories 1-2) already work.

**Independent Test**: Can be fully tested by submitting a prompt whose attack instruction is
Base64-encoded and confirming the same rule that catches the plain-text version also catches
the encoded version when normalization is enabled.

**Acceptance Scenarios**:

1. **Given** normalization is enabled, **When** a prompt contains a Base64-encoded instruction
   that would otherwise match a rule, **Then** the rule fires on the decoded content.
2. **Given** normalization is disabled, **When** the same encoded prompt is evaluated,
   **Then** the rule does not fire on the hidden content.

---

### Edge Cases

- What happens when a rule's detector pipeline itself errors (e.g., a malformed regex, a
  missing model file)? The overall decision MUST fail closed (treated as block) and the error
  MUST be visible in the decision trace, not silently swallowed.
- How does the system handle a prompt that matches zero rules in a chain using default-allow
  semantics vs. a chain using default-deny semantics? Each chain's declared default MUST be
  honored explicitly.
- How does the system handle conflicting verdicts from different detector nodes within one
  rule (e.g., one node says allow, another abstains)? The rule's declared pipeline order and
  short-circuit semantics MUST determine the outcome deterministically.
- What happens when the same prompt is evaluated twice against the same rule/chain? The
  library MUST produce the same verdict both times (deterministic given the same inputs and
  configuration).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST load rule and chain definitions from version-controlled,
  human-readable structured files rather than requiring rules to be written as code.
- **FR-002**: The library MUST evaluate a submitted prompt against a selected chain and return
  a decision of "allow" or "block", including which rule(s) and detector node(s) contributed
  to the decision.
- **FR-003**: Each rule MUST support an ordered pipeline of detector nodes and MUST short-
  circuit remaining nodes once a preceding node in the pipeline produces a determinative block.
- **FR-004**: A chain MUST support at least two composition modes: an ordered, first-match
  mode with a configurable default outcome, and an expression mode that combines named rules
  with boolean logic.
- **FR-005**: The library MUST provide a lexical/pattern-based detector type, a protected-
  health-identifier detector type, and a natural-language scope-judgment detector type, with
  the pipeline able to mix them within one rule.
- **FR-006**: The library MUST support validating a rule's own declared example prompts
  (in-scope and out-of-scope) and reporting whether each produces the expected verdict.
- **FR-007**: The library MUST support an optional normalization step that decodes common
  obfuscation techniques (Base64, hex, ROT13, homoglyph substitution, leetspeak, zero-width
  characters) prior to detection, and detection MUST be able to run against the normalized
  form.
- **FR-008**: The protected-health-identifier detector MUST cover the standard 18-identifier
  safe-harbor category set, reporting each match's category without requiring model retraining.
- **FR-009**: Every evaluation MUST produce a decision trace record (which rules/nodes ran,
  their individual verdicts, and the final decision) suitable for writing to an audit log.
- **FR-010**: The library MUST fail closed: if a detector node or chain evaluation errors or
  cannot reach a determinate verdict, the overall decision MUST default to "block" rather than
  silently allowing the request through.
- **FR-011**: The library MUST expose its evaluation capability as an importable API usable
  directly from Python application code (no separate network hop required to get a decision).
- **FR-012**: The library MUST allow repeated evaluation of the same prompt/rule/chain
  combination to skip redundant detector work when a prior verdict for that exact combination
  is already known within the same evaluation session.

### Key Entities

- **Rule**: A single policy unit with a declared natural-language scope, an ordered detector
  pipeline, and example prompts (in-scope/out-of-scope) used both to document and to test it.
- **Chain**: A composition of one or more rules into a single allow/block decision, in either
  ordered or boolean-expression mode, with a declared default outcome.
- **Detector Node**: One step within a rule's pipeline (e.g., pattern match, protected-
  identifier scan, scope judgment) that returns a verdict, and optionally a confidence and
  rationale.
- **Decision Trace**: The record of a single evaluation — which rules and nodes ran, their
  individual verdicts, and the final allow/block outcome and reason.
- **Identifier Panel**: The set of protected-information categories (e.g., the standard
  18-identifier safe-harbor set) the protected-identifier detector checks for.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A policy author can define a new rule, including working examples, and get a
  pass/fail validation result without writing procedural code.
- **SC-002**: Prompts containing a known attack pattern are blocked, and ordinary prompts are
  allowed, with the responsible rule identifiable from the decision alone, for at least 95%
  of a representative test corpus.
- **SC-003**: Evaluation of a prompt against a chain returns a decision without the caller
  needing to inspect or reason about internal detector implementation details.
- **SC-004**: A prompt whose attack instruction is hidden via a supported obfuscation
  technique is caught at the same rate as its plain-text equivalent when normalization is
  enabled.
- **SC-005**: The added time to evaluate a typical prompt against a typical rule set is small
  enough that it does not become the dominant source of latency in a request that also calls
  an LLM.
- **SC-006**: Every blocked decision can be explained after the fact from its recorded trace
  alone, without re-running the evaluation.

## Assumptions

- This port targets feature parity with the reference library's rule/chain evaluation model,
  protected-health-identifier panel, and de-obfuscation normalization; it does not require
  reproducing the reference implementation's benchmark harness or research paper results.
- "Efficient" is interpreted as: evaluation overhead should be negligible relative to the
  latency of the downstream LLM call it guards, and expensive detector nodes should only run
  when cheaper nodes in the same pipeline have not already reached a determinate verdict.
- The library is consumed as an importable Python package within an application process; a
  standalone network-facing proxy service is out of scope for this feature and may be built
  as a separate, later feature on top of this library.
- Wire-format adapters for specific LLM provider APIs (OpenAI, Anthropic, Gemini, Ollama) are
  out of scope for this feature; this port focuses on the evaluation engine, rule/chain model,
  and detector library that such adapters would sit in front of.
- Rule and chain definitions are authored in the same structured file format as the reference
  library so existing rule sets can be reused with minimal translation.
