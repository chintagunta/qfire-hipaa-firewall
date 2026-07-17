# Data Model: QFIRE Python Port

Entities below map directly to spec Key Entities. All are represented as stdlib
`dataclasses` (per research.md) constructed only after manual validation of the parsed
YAML dict — no dataclass is ever instantiated in a partially-invalid state.

## Rule

Represents FR-001, FR-003, FR-006.

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Unique within a loaded rule set; required. |
| `scope` | `str` | Natural-language declared scope; required (Constitution Principle II). |
| `short_circuit` | `str` | One of `"stop_on_first_block"` \| `"run_all"`; default `"stop_on_first_block"`. |
| `pipeline` | `list[DetectorNode]` | Ordered, cheapest-first by author convention (FR-003); at least one node required. |
| `exemplars` | `ExemplarSet` | In-scope and out-of-scope example prompts (FR-006). |

**Validation rules**:
- `id`, `scope`, and a non-empty `pipeline` are required; missing/empty → validation error
  naming the file and field (FR-001 acceptance scenario 2).
- Each pipeline entry must resolve to a known detector node `type`.
- `exemplars` must contain at least one entry in either `in_scope` or `out_of_scope` to be
  validate-able, though a fully useful rule has both (Story 2 acceptance scenario 1).

## ExemplarSet

| Field | Type | Notes |
|---|---|---|
| `in_scope` | `list[str]` | Prompts expected to yield `allow`. |
| `out_of_scope` | `list[str]` | Prompts expected to yield `block`. |

## DetectorNode

Base contract every node type (`pattern`, `phi`, `classifier`, `judge`) implements.

| Field | Type | Notes |
|---|---|---|
| `type` | `str` | One of `"pattern"` \| `"phi"` \| `"classifier"` \| `"judge"`. |
| `config` | `dict` | Type-specific parameters (e.g., `deny` patterns for `pattern`; `threshold` for `classifier`). |

**Runtime verdict** (not persisted, produced per evaluation): `verdict` (`"block"` \|
`"allow"` \| `"abstain"`), `confidence` (`float`, optional), `rationale` (`str`, optional),
`latency_ms` (`float`).

**Validation rules**: `pattern` requires at least one of `deny`/`allow` pattern lists;
`phi` requires no config (fixed 18-identifier panel, spec FR-008) or an explicit subset
list; `classifier` requires a `threshold` in `[0, 1]`; `judge` requires an endpoint
reference resolvable at evaluation time (may be deferred to runtime config, not the YAML
file, to avoid embedding secrets/URLs in version-controlled policy).

## Chain

Represents FR-002, FR-004.

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Unique; required. |
| `mode` | `str` | `"ordered"` \| `"expression"`; required. |
| `default` | `str` | `"allow"` \| `"block"`; required for `ordered` mode (edge case: default must be explicit). |
| `rules` | `list[str]` | Rule IDs, required for `ordered` mode. |
| `groups` | `dict[str, str]` | Named reusable boolean sub-expressions; only for `expression` mode. |
| `expression` | `str` | Boolean expression over rule IDs / groups; required for `expression` mode. |
| `fail_policy` | `str` | `"fail_closed"` (default, constitution Principle V) \| explicit `"fail_open"` opt-in with a required justification comment. |

**Validation rules**: `mode="ordered"` requires `rules` + `default`; `mode="expression"`
requires `expression` (and optionally `groups`); all referenced rule IDs must exist in the
loaded rule set or loading fails with a clear error.

## DecisionTrace

Represents FR-009, spec Success Criterion SC-006, constitution Principle V.

| Field | Type | Notes |
|---|---|---|
| `prompt_hash` | `str` | SHA-256 of the evaluated prompt (not the raw prompt, for privacy in logs). |
| `chain_id` | `str` | Which chain was evaluated. |
| `decision` | `str` | `"allow"` \| `"block"`. |
| `node_results` | `list[NodeResult]` | Every node that ran, in execution order, with its verdict. |
| `fired_rule_id` | `str \| None` | The rule that produced the terminal block, if blocked. |
| `error` | `str \| None` | Populated when fail-closed triggered due to an evaluation error (FR-010). |
| `timestamp` | `str` | ISO-8601, UTC. |

`NodeResult`: `{rule_id, node_type, verdict, confidence, rationale, latency_ms}` — the
per-node runtime verdict shape above, attributed to its owning rule.

**Persistence**: appended as one JSON line per evaluation to the configured audit log file
(FR-009) — immutable, append-only by convention (the library does not overwrite or rewrite
prior lines).

## Identifier Panel (PHI)

Fixed reference data, not user-authored: the 18 HIPAA safe-harbor identifier categories
(names, geographic subdivisions smaller than state, dates, phone/fax, email, SSN, MRN,
health-plan beneficiary numbers, account numbers, certificate/license numbers, vehicle
identifiers, device identifiers, URLs, IP addresses, biometric identifiers, full-face
photos, other unique identifying numbers, and — the panel's own detector class — any
combination thereof). Each category has a matcher (pattern-based where feasible) and a
category label surfaced in `NodeResult.rationale` (FR-008).

## Relationships

```text
Chain 1---* Rule (by id, ordered mode) / Rule referenced in boolean expression (expression mode)
Rule 1---* DetectorNode (ordered pipeline)
Rule 1---1 ExemplarSet
DecisionTrace 1---* NodeResult (attributed back to Rule/DetectorNode)
DetectorNode(type=phi) ---> Identifier Panel (fixed reference data, not stored per-rule)
```

No state transitions apply — every entity here is either static configuration (Rule,
Chain, ExemplarSet, Identifier Panel) or a one-shot evaluation record (DecisionTrace,
NodeResult); nothing is mutated in place after creation.
