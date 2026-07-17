# Implementation Plan: QFIRE Python Port

**Branch**: `001-qfire-python-port` | **Date**: 2026-07-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-qfire-python-port/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Port QFIRE's declarative rule/chain evaluation engine, protected-health-identifier (PHI)
panel, and de-obfuscation normalization to a Python library, importable directly into an
application process (no proxy service). Rules and chains stay YAML-authored and
example-driven; detector nodes run cheapest-first with short-circuiting. Dependencies are
kept minimal per the user's request: `PyYAML` for policy files, `regex` for pattern
detectors, `onnxruntime` (CPU execution provider) + `tokenizers` for the local injection
classifier, and stdlib-only (`urllib.request`, `dataclasses`) everywhere else.

## Technical Context

**Language/Version**: Python ≥3.12 (matches existing `pyproject.toml` / `.python-version`)

**Primary Dependencies**: `PyYAML` (rule/chain parsing), `regex` (pattern detector nodes,
stdlib `re` as a no-dependency fallback), `onnxruntime` CPU build (local classifier
inference), `tokenizers` (classifier pre-processing); stdlib `dataclasses` and
`urllib.request` for everything else — see [research.md](./research.md).

**Storage**: Files only — YAML rule/chain definitions on disk; JSON-lines audit log file. No
database.

**Testing**: `pytest`, with each rule's YAML `exemplars` consumed as parametrized test cases
(constitution Principle III).

**Target Platform**: Any platform with a Python ≥3.12 interpreter and a CPU-only
`onnxruntime` wheel (Linux/macOS/Windows, x86_64/arm64); no GPU requirement.

**Project Type**: Library (importable Python package; no CLI or network service in this
feature — see spec Assumptions).

**Performance Goals**: Evaluation overhead per prompt must stay negligible relative to a
downstream LLM call (spec SC-005) — target: sub-100ms p95 for a typical chain (a few
regex/PHI nodes plus one ONNX classifier node) on a modern CPU, with cheap nodes running in
low single-digit milliseconds.

**Constraints**: No PyTorch/GPU dependency; no network-facing service; fail-closed on any
detector error (constitution Principle V, spec FR-010); rule/chain YAML schema must stay
compatible with the reference QFIRE format (spec Assumptions).

**Scale/Scope**: Parity-scoped port — rule/chain evaluation engine, PHI safe-harbor panel
(18 identifiers), de-obfuscation normalization. Out of scope: benchmark harness, research
reproduction, provider wire-adapters, standalone proxy (spec Assumptions).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Policy Is Data, Not Code | Rules/chains authored as YAML; engine interprets them; exemplars double as test fixtures (FR-001, FR-006) | PASS |
| II. Positive-Security Scope Enforcement | Rule schema requires a declared scope; scope-judge detector type included alongside blockers (FR-005) | PASS |
| III. Test-First Development | Rule exemplars become pytest parametrized cases before/alongside implementation; TDD workflow adopted for engine code | PASS |
| IV. Cheap-Before-Expensive, Bounded Latency | Pipeline execution order is cheapest-first with short-circuit (FR-003); ONNX CPU chosen over PyTorch specifically for bounded latency | PASS |
| V. Auditable, Fail-Closed Decisions | DecisionTrace captures per-node verdicts; FR-010 mandates fail-closed on error; no silent degradation (classifier-absent fallback is reported, per research.md) | PASS |

No violations — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-qfire-python-port/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── qfire/
    ├── __init__.py          # public API: evaluate(), load_chain(), load_rule()
    ├── rules.py              # Rule dataclass + YAML loading/validation
    ├── chains.py              # Chain dataclass (ordered/expression modes) + evaluation
    ├── nodes/
    │   ├── __init__.py        # DetectorNode protocol/base
    │   ├── pattern.py          # regex/stdlib-re deny-list detector
    │   ├── phi.py              # HIPAA safe-harbor 18-identifier detector
    │   ├── classifier.py       # onnxruntime + tokenizers injection classifier
    │   └── judge.py            # LLM scope-judge (urllib.request HTTP call)
    ├── normalize.py            # de-obfuscation pass (base64/hex/rot13/homoglyph/leetspeak/zero-width)
    ├── trace.py                # DecisionTrace + audit-log writer (JSON-lines)
    └── errors.py               # validation + fail-closed error types

tests/
├── unit/                   # per-module unit tests (nodes, normalize, trace)
├── integration/            # full evaluate() flows against sample chains
└── rules/                  # exemplar-driven parametrized tests generated from rule YAML

rules/                       # shipped example rule/chain YAML (ported subset from reference)
└── healthcare/
    └── phi_panel.yaml
```

**Structure Decision**: Single-project library layout (`src/qfire/`), matching the existing
`pyproject.toml` at the repo root. No frontend/backend or mobile split applies — this is a
pure Python library consumed via import (spec Assumptions: proxy/adapters explicitly
deferred). `rules/` at the repo root holds shipped example policy so the library is usable
out of the box without requiring every consumer to author rules from scratch.

## Complexity Tracking

> Not applicable — no Constitution Check violations.
