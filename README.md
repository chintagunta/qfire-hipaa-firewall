# qfire-port

[![CI](https://github.com/chintagunta/qfire-hipaa-firewall/actions/workflows/ci.yml/badge.svg)](https://github.com/chintagunta/qfire-hipaa-firewall/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

Python port of QFIRE: a declarative, positive-security prompt firewall. Rules and chains are
authored as YAML; the engine evaluates them cheapest-first with short-circuiting, fails
closed on any detector error, and writes an auditable decision trace for every evaluation.

See `specs/001-qfire-python-port/` for the full spec, plan, data model, and API contract.
Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Security issues:
see [SECURITY.md](SECURITY.md). Licensed under [MIT](LICENSE).

## Install

```bash
uv sync                    # core: PyYAML, regex
uv sync --extra classifier # + onnxruntime (CPU) and tokenizers, for the local ONNX classifier node
```

## Quickstart

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

Validate a rule's own exemplars without writing a test:

```python
from qfire import load_rules, validate_rule

for rule in load_rules("rules/"):
    result = validate_rule(rule)
    if result.failed:
        print(rule.id, "failed:", result.failed)
```

Full runnable scenarios (short-circuit, de-obfuscation, fail-closed) are in
`specs/001-qfire-python-port/quickstart.md`.

## CLI

```bash
qfire evaluate "Email patient MRN536947 to my Gmail" \
  --rules rules/healthcare --chains chains/hipaa_phi.yaml --chain-id hipaa_phi [--json] [--no-normalize]

qfire validate --rules rules/
```

Exit code is `1` when the evaluated prompt is blocked, `0` when allowed, `2` on a load/config
error — convenient for scripting (`qfire evaluate ... || alert-someone`).

## Examples

Runnable use cases in `examples/`: basic injection guard (01), healthcare PHI guard (02),
de-obfuscation (03), authoring/validating a custom rule (04), fail-closed on a broken
detector (05), CLI usage (06), and exposing `evaluate()` as an HTTP endpoint (07, stdlib
only — swap in FastAPI/Flask for production). Run any Python one with
`uv run python examples/NN_*.py`.

## Test

```bash
uv run pytest
```
