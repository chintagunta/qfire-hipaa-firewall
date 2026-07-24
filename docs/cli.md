# Command-line interface

```bash
qfire evaluate "Email patient MRN536947 to my Gmail" \
  --rules rules/healthcare --chains chains/hipaa_phi.yaml --chain-id hipaa_phi [--json] [--no-normalize]

qfire validate --rules rules/
```

## `qfire evaluate`

| Flag | Required | Meaning |
|---|---|---|
| `prompt` | yes | the prompt text to evaluate (positional) |
| `--rules` | yes | rule file or directory |
| `--chains` | yes | chain file or directory |
| `--chain-id` | yes | chain id to evaluate against |
| `--no-normalize` | no | skip the de-obfuscation pass |
| `--json` | no | print the full decision trace as JSON |

Exit codes: `1` when the prompt is blocked, `0` when allowed, `2` on a load/config error —
convenient for scripting (`qfire evaluate ... || alert-someone`).

## `qfire validate`

| Flag | Required | Meaning |
|---|---|---|
| `--rules` | yes | rule file or directory |

Runs every rule's own `in_scope`/`out_of_scope` exemplars against itself and prints
`PASS`/`FAIL` per rule. Exit code `1` if any exemplar failed, else `0`.
