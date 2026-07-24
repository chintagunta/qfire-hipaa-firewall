# Contributing

## Setup

```bash
uv sync --group dev
uv run pytest
```

## Making a change

- Rules/detectors: policy is data (constitution Principle I) — prefer adding/editing a YAML
  rule under `rules/` over hard-coding logic. Every rule needs both an `in_scope` and an
  `out_of_scope` exemplar; `uv run qfire validate --rules rules/` must pass before you open a PR.
- Code: this project follows test-first development (constitution Principle III,
  NON-NEGOTIABLE). Write a failing test before the implementation.
- New detector node type: order it cheapest-first in any rule pipeline that uses it
  (constitution Principle IV), and report its measured latency in the PR description.
- Any new failure path must fail closed, not open (constitution Principle V) — a broken
  node should block and record the error, never silently allow.

See `.specify/memory/constitution.md` for the full governance rules and
`specs/001-qfire-python-port/` for the design docs behind the current architecture.

## Before opening a PR

```bash
uv run pytest
uv run qfire validate --rules rules/
```

## Reporting a security issue

See [SECURITY.md](SECURITY.md) — do not open a public issue for a vulnerability in the
firewall's detection logic itself.
