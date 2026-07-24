<!--
Sync Impact Report
Version change: none → 1.0.0 (initial ratification)
Modified principles: n/a (new document)
Added sections: Core Principles (5), Additional Constraints, Development Workflow, Governance
Removed sections: none
Templates requiring updates:
  ✅ .specify/templates/plan-template.md (generic Constitution Check gate, no changes needed)
  ✅ .specify/templates/spec-template.md (no principle-specific refs found)
  ✅ .specify/templates/tasks-template.md (task categories already include test/policy work)
  ⚠ README.md — still a stub; recommend adding project description referencing this constitution
Follow-up TODOs: none
-->

# QFIRE-Port Constitution

## Core Principles

### I. Policy Is Data, Not Code
Firewall rules, chains, and scope declarations MUST be expressed as version-controlled,
declarative data (YAML or equivalent structured format) that the engine interprets at
runtime. Business logic for detection MUST NOT be hard-coded as one-off conditionals
in application code when a rule/chain definition can express it. Every rule's exemplars
double as test fixtures and MUST be runnable as such.
Rationale: Declarative policy is auditable, diffable, and unit-testable by a compliance
reviewer without reading source code — this is QFIRE's core differentiator over
code/model-based guardrail frameworks.

### II. Positive-Security Scope Enforcement
Every rule MUST declare an explicit, natural-language scope describing what is permitted;
detectors judge conformance to that declared scope rather than only scanning for known
attack signatures. Negative-only (blocklist-only) detection MUST NOT be the sole
mechanism protecting a sensitive domain (e.g., PHI, cross-tenant data).
Rationale: Most real-world clinical/enterprise threats carry no attack signal and evade
pure injection classifiers; scope-based positive security closes that gap.

### III. Test-First Development (NON-NEGOTIABLE)
TDD is mandatory for all rule, detector, and engine logic: tests (including rule exemplar
fixtures) are written and observed failing before implementation code is written.
Red-Green-Refactor MUST be followed strictly. No rule ships without both an `in_scope`
and an `out_of_scope`/`deny` exemplar exercised as an automated test.
Rationale: A firewall that silently regresses is worse than no firewall; tests are the
only guarantee that a rule change didn't reopen a closed threat class.

### IV. Cheap-Before-Expensive, Bounded Latency
Detector pipelines MUST order nodes cheapest-first (lexical/regex before ML classifier
before LLM judge) with short-circuit on first block. Any change that adds a detector
node MUST report its measured latency impact (p50/p95/p99) before merge. No component
may introduce unbounded-latency network calls in the hot path without a documented
timeout and fallback.
Rationale: Security value collapses if the firewall becomes the bottleneck; latency
budgets are a first-class requirement, not an afterthought.

### V. Auditable, Fail-Closed Decisions
Every firewall decision (allow/block) MUST be explainable via a per-rule trace and
written to an immutable audit log before the request is forwarded or refused. Chains
MUST default to fail-closed on error or ambiguous evaluation, never fail-open. Silent
degradation (e.g., falling back from a real classifier to a weaker one) MUST be surfaced
in the decision trace, never hidden.
Rationale: Regulatory and clinical-safety contexts (HIPAA minimum-necessary, patient
safety) require decisions to be reconstructable after the fact, not just correct in
aggregate.

## Additional Constraints

- Target stack: Rust (Tokio async runtime) for the engine/proxy/CLI; no Python in the
  request hot path. Python/PyTorch usage is confined to offline baseline comparisons
  and benchmarking, never to production request handling.
- PHI and other regulated-identifier detection MUST match the applicable safe-harbor
  identifier set (e.g., HIPAA's 18 identifiers) exactly — partial or approximate
  identifier coverage MUST be called out explicitly in documentation, not silently shipped.
- All benchmark corpora and evaluation manifests MUST be versioned in-repo so that
  reported metrics are reproducible end-to-end without paid/external API dependencies.

## Development Workflow

- Every new or modified rule/chain requires: (1) a failing exemplar test, (2) the
  minimal pipeline/config to pass it, (3) a latency measurement if a new detector node
  type is introduced.
- Code review MUST verify: policy expressed as data where possible, fail-closed behavior
  on error paths, and that the audit trail captures the decision rationale.
- Breaking changes to rule/chain schema require a MAJOR version bump of this
  constitution's governed conventions and a migration note for existing rule files.

## Governance

This constitution supersedes ad hoc practice for this repository. Amendments require:
a written rationale, an update to this file with a version bump per semantic versioning
(MAJOR: incompatible principle removal/redefinition; MINOR: new principle or materially
expanded guidance; PATCH: clarification/wording), and propagation to any dependent
templates in `.specify/templates/`. All PRs and reviews MUST verify compliance with the
Core Principles above; deviations require explicit justification recorded in the PR
description. Use `CLAUDE.md` for day-to-day runtime development guidance that supplements,
but does not override, this document.

**Version**: 1.0.0 | **Ratified**: 2026-07-17 | **Last Amended**: 2026-07-17
