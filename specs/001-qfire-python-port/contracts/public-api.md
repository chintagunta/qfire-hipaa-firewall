# Contract: `qfire` Public Python API

This is a library, not a network service — its "contract" is the importable surface other
Python code depends on. Signatures are illustrative (types only); implementation bodies are
not part of this contract and belong to the implementation phase.

## Loading policy

```python
def load_rules(path: str | Path) -> RuleSet:
    """Load and validate all rule YAML files under `path`.
    Raises RuleValidationError (with file + field) on any malformed rule (FR-001)."""

def load_chains(path: str | Path, rules: RuleSet) -> ChainSet:
    """Load and validate chain YAML files, resolving rule-id references against `rules`.
    Raises ChainValidationError on unknown rule references or malformed mode config."""
```

## Evaluating a prompt

```python
def evaluate(prompt: str, chain_id: str, chains: ChainSet, *, normalize: bool = True) -> Decision:
    """Evaluate `prompt` against the named chain.

    - Runs the chain's rules per its mode (ordered/expression) (FR-002, FR-004).
    - Within each rule, runs pipeline nodes cheapest-first with short-circuit (FR-003).
    - When `normalize=True`, detection also runs against the de-obfuscated view of the
      prompt (FR-007); `normalize=False` skips this pass.
    - Never raises for a detector-level failure: any node/chain error is captured and the
      returned Decision has `.decision == "block"` with `.trace.error` populated
      (FR-010 fail-closed). Raises only for programmer errors (unknown chain_id).
    - Always writes one DecisionTrace record to the configured audit log before returning
      (FR-009).
    """
```

## Validating a rule's own exemplars

```python
def validate_rule(rule: Rule) -> ExemplarValidationResult:
    """Evaluate every exemplar in `rule.exemplars` against `rule` alone (not a full chain)
    and report per-exemplar pass/fail against the expected verdict (FR-006, Story 2)."""
```

## Return types (shape only — see data-model.md for full field lists)

```python
@dataclass(frozen=True, slots=True)
class Decision:
    decision: Literal["allow", "block"]
    fired_rule_id: str | None
    trace: DecisionTrace

@dataclass(frozen=True, slots=True)
class ExemplarValidationResult:
    rule_id: str
    passed: list[str]     # exemplar prompts that matched expected verdict
    failed: list[tuple[str, str]]   # (exemplar prompt, actual verdict) mismatches
```

## Error types

```python
class QfireError(Exception): ...
class RuleValidationError(QfireError): ...    # includes .file, .field
class ChainValidationError(QfireError): ...   # includes .file, .field
```

`RuleValidationError`/`ChainValidationError` are raised at **load time** only — never during
`evaluate()`, which is fail-closed instead of raising (FR-010, edge case: detector pipeline
errors).

## Consumer usage pattern (illustrative, not exhaustive)

```python
rules = load_rules("rules/")
chains = load_chains("chains/", rules)

decision = evaluate(user_prompt, chain_id="hipaa_phi", chains=chains)
if decision.decision == "block":
    raise Refused(decision.fired_rule_id)
# else: forward the original request downstream unchanged
```

No REST/gRPC/CLI surface is part of this contract (spec Assumptions: proxy service and
provider wire-adapters are out of scope for this feature).
