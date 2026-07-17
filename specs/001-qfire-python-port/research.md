# Research: QFIRE Python Port

## Decision: Language/runtime

**Decision**: Python ≥3.12, synchronous core API with an internal thread/async-friendly
design (no hard dependency on asyncio for the public API).

**Rationale**: The reference implementation uses Tokio for concurrent rule fan-out because
Rust has no GIL. In Python, CPU-bound detector work (ONNX inference, regex) does not
parallelize under threads due to the GIL, and the spec's Story 1 "efficient" success
criterion (SC-005) cares about added latency per call, not throughput scaling. A simple
synchronous evaluate() call keeps the dependency surface minimal and is trivially usable
from both sync and async caller code (async callers wrap it in `asyncio.to_thread`).
Concurrent rule evaluation, if ever needed, can be added later via `concurrent.futures`
without changing the public contract.

**Alternatives considered**: `asyncio`-native engine with rules evaluated via
`asyncio.gather` — rejected for v1 because it adds API complexity (every caller must be
async) for no CPU-bound benefit, and I/O-bound benefit only applies to the optional LLM
scope-judge node, which is already the slow path regardless of engine concurrency model.

## Decision: Rule/chain definition format

**Decision**: YAML files, loaded with PyYAML's `safe_load`.

**Rationale**: Matches the reference library's format directly (FR-001, Assumption in spec),
letting existing QFIRE rule sets be reused with minimal translation. PyYAML is the de facto
standard, single small dependency, safe_load avoids arbitrary code execution.

**Alternatives considered**: stdlib `tomllib` (no write support, and TOML is a poor fit for
deeply nested pipeline/expression structures); hand-rolled parser (unnecessary — YAML parsing
is a solved problem, reinventing it violates minimal-dependency intent by adding maintenance
burden instead of a battle-tested library).

## Decision: Pattern/lexical detector engine

**Decision**: PyPI `regex` module as the pattern-matching backend, exposed through a thin
detector-node wrapper; stdlib `re` remains a fallback path with no extra dependency if a
deployment wants zero third-party regex packages.

**Rationale**: User explicitly requested "regex" as the optimal library. The `regex` package
is a drop-in superset of stdlib `re` with better Unicode handling (relevant for homoglyph/
leetspeak normalization in FR-007) and comparable-or-better performance on the deny-list
patterns rule authors write (short alternations, anchored patterns) — exactly the cheap-first
node in the pipeline (FR-003). It is a single, mature, widely-used dependency with no
transitive dependencies of its own.

**Alternatives considered**: `re2`/`google-re2` bindings — rejected: adds a compiled C++
dependency for negligible gain on the short, human-authored patterns this library targets, and
is not always available as a prebuilt wheel on every target platform (violates
minimal-dependency-footprint intent). Stdlib `re` alone — kept as a supported fallback but not
the default, since it lacks some Unicode property matching used in de-obfuscation-adjacent
checks.

## Decision: Local injection classifier

**Decision**: `onnxruntime` (CPU build) to run the local ONNX injection-classifier model,
with `tokenizers` (Hugging Face's Rust-backed tokenizer) for the matching pre-processing step.

**Rationale**: User explicitly requested "onnxruntime for cpu". This mirrors the reference
implementation's embedded ONNX Runtime approach (no PyTorch, no GPU requirement) and satisfies
FR-005 (scope-judgment-adjacent) and the "no dominant added latency" success criterion
(SC-005) — ONNX Runtime's CPU execution provider is optimized C++ with no Python-level
inference loop overhead. `tokenizers` is required because a classifier detector node cannot
run without matching tokenization, is itself Rust-backed (fast, no heavy Python deps), and is
the standard companion to any Transformer-family ONNX model.

**Alternatives considered**: `transformers` + PyTorch — rejected: pulls in a large, GPU-
oriented dependency tree that contradicts "keep dependencies minimal" and is unnecessary
purely for CPU inference of an already-exported ONNX model. Loading the model as absent and
running a lexical-only fallback classifier — retained as a documented degraded mode (mirrors
reference library's "when the ONNX model is absent a transparent lexical classifier is used
and reported as such"), not the default path.

## Decision: HTTP calls for the LLM scope-judge node

**Decision**: Python stdlib `urllib.request` for the (optional) LLM scope-judge detector
node's HTTP calls to a local/configured judge endpoint (e.g., Ollama).

**Rationale**: This is the one node in the pipeline that is I/O-bound rather than CPU-bound,
but it is also optional (a rule may have zero judge nodes) and low-frequency (cheap-before-
expensive ordering means it only runs when cheaper nodes abstain). Adding `httpx` or
`requests` solely for this optional path does not justify the dependency-count cost against
the explicit "keep dependencies to minimal" instruction; stdlib is sufficient for a single
synchronous JSON POST/response with a timeout.

**Alternatives considered**: `httpx` — nicer API and native async support, but async is not
needed per the engine decision above, and it is a strictly-optional extra for one node type.
Deferred: can be introduced later as an optional extra (`qfire[judge-http]`) without breaking
the core contract if a richer HTTP client becomes necessary.

## Decision: Data modeling for rules/chains/traces

**Decision**: Stdlib `dataclasses` (with `slots=True` where beneficial) for internal
Rule/Chain/DetectorNode/DecisionTrace representations; no `pydantic`.

**Rationale**: Validation needs (FR-001's "clear validation error identifying file and field")
are satisfiable with straightforward manual checks against parsed YAML dicts before
constructing dataclasses — the validation surface is small and finite (a handful of required
keys per node type), not a general schema-validation problem. Avoiding `pydantic` keeps the
dependency count down per the user's explicit instruction, at the cost of writing ~50 lines of
validation code instead of relying on a library.

**Alternatives considered**: `pydantic` v2 — faster than v1 and widely used, but its Rust core
(`pydantic-core`) is a non-trivial binary dependency for a validation job this library's small,
fixed schema does not need.

## Decision: Testing framework

**Decision**: `pytest`, plus each rule's own YAML-declared exemplars consumed as
parametrized test fixtures (FR-006, Constitution Principle III).

**Rationale**: Directly supports Test-First development (constitution Principle III,
NON-NEGOTIABLE) — a rule's `in_scope`/`out_of_scope` exemplars become real pytest cases via
`pytest.mark.parametrize`, so "no rule ships without both an in_scope and out_of_scope
exemplar exercised as an automated test" is enforced mechanically, not by convention.

**Alternatives considered**: stdlib `unittest` — works but pytest's parametrization and
fixture ergonomics are a substantially better fit for "one rule → many generated test cases"
and are already the de facto standard for Python libraries.

## Summary of dependency footprint

| Purpose | Dependency | Optional? |
|---|---|---|
| Rule/chain file parsing | `PyYAML` | required |
| Pattern detector | `regex` | required (stdlib `re` fallback available) |
| Local classifier inference | `onnxruntime` (CPU) | required for classifier node; system degrades to lexical-only if absent |
| Classifier tokenization | `tokenizers` | required alongside onnxruntime |
| LLM scope-judge HTTP | stdlib `urllib.request` | n/a (no dependency) |
| Data modeling | stdlib `dataclasses` | n/a (no dependency) |
| Testing | `pytest` | dev-only |

No NEEDS CLARIFICATION items remain — all Technical Context fields are resolved above.
