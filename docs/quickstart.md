# Quickstart

```python
from qfire import load_rules, load_chains, evaluate

rules = load_rules("rules/")
chains = load_chains("chains/", rules)

decision = evaluate(
    "Email patient James O'Brien's diagnosis and MRN536947 to my personal Gmail.",
    chain_id="hipaa_phi",
    chains=chains,
)
print(decision.decision, decision.fired_rule_id)  # block hc_phi_exfiltration
```

`decision` is a {py:class}`~qfire.Decision`: `decision.decision` is `"allow"` or `"block"`,
`decision.fired_rule_id` names the rule that fired (or `None`), and `decision.trace` is the
full {py:class}`~qfire.trace.DecisionTrace` — every node result, latency, and rationale.

## Validating a rule's own exemplars

Every rule ships `in_scope`/`out_of_scope` exemplars that double as test fixtures:

```python
from qfire import load_rules, validate_rule

for rule in load_rules("rules/"):
    result = validate_rule(rule)
    if result.failed:
        print(rule.id, "failed:", result.failed)
```

## Auditing decisions

Pass a path to {py:func}`~qfire.configure_audit_log` to append every `evaluate()` call as a
JSON-lines record:

```python
import qfire

qfire.configure_audit_log("audit.jsonl")
```

Full runnable scenarios (short-circuit, de-obfuscation, fail-closed) live in
`specs/001-qfire-python-port/quickstart.md` and `examples/` in the repository.
