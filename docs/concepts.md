# Concepts: rules, chains, and detector nodes

## Rules

A {py:class}`~qfire.rules.Rule` declares a natural-language `scope` and an ordered `pipeline`
of detector nodes. It is loaded from YAML (policy is data, not code):

```yaml
# rules/healthcare/phi_panel.yaml
id: hc_no_diagnosis
scope: "General health info only; no diagnosis or symptom interpretation."
short_circuit: stop_on_first_block
pipeline:
  - type: judge
exemplars:
  in_scope: ["What is hypertension and its lifestyle factors?"]
  out_of_scope: ["I have fever and a stiff neck - do I have meningitis?"]
```

Each `pipeline` entry runs in order; with `short_circuit: stop_on_first_block` (the default)
the first node that blocks stops the rest. Every rule must ship at least one `in_scope` or
`out_of_scope` exemplar — {py:func}`~qfire.validate_rule` runs these as fixtures.

Node `type` must be one of `pattern`, `phi`, `classifier`, `judge` — see
{doc}`api/nodes` for what each detects.

## Chains

A {py:class}`~qfire.chains.Chain` composes rules into one terminal decision, in one of two
modes:

- **`ordered`** — first matching rule wins (iptables-style), with a configurable `default`
  (`allow`/`block`).
- **`expression`** — a boolean expression over named rules and reusable `groups`, e.g.
  `injection_guard AND (marketing OR support)`.

```yaml
# chains/hipaa_phi.yaml
id: hipaa_phi
mode: expression
fail_policy: fail_closed
expression: >
  injection_instruction_override AND hc_no_diagnosis AND hc_phi_other_patient_record
```

## Fail-closed

Any detector-level error is caught and recorded on the {py:class}`~qfire.trace.DecisionTrace`
rather than raised — a broken node blocks the request and records the error, it never
silently allows. {py:func}`~qfire.evaluate` only raises `KeyError` for an unknown `chain_id`.

## De-obfuscation normalization

When `evaluate(..., normalize=True)` (the default) allows a prompt, {py:func}`~qfire.normalize.normalize`
also runs against it: it strips zero-width characters, folds homoglyphs/leetspeak to ASCII,
and decodes Base64/hex/ROT13 runs. If the normalized prompt evaluates to `block`, that
stricter result is used instead — so an obfuscated payload can't slip through the raw text.
