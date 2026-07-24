# qfire-hipaa-firewall

Python port of QFIRE: a declarative, positive-security prompt firewall. Rules and chains
are authored as YAML; the engine evaluates them cheapest-first with short-circuiting, fails
closed on any detector error, and writes an auditable decision trace for every evaluation.

```{toctree}
:maxdepth: 2
:caption: User Guide

installation
quickstart
concepts
cli
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/qfire
api/nodes
api/errors
```

```{toctree}
:maxdepth: 2
:caption: Contributor Guide

contributing
```

## Background

The design is based on the original [QFIRE research paper](https://github.com/chintagunta/qfire-hipaa-firewall/blob/main/docs/qfire.md)
(Rust reference implementation); this package is a Python port of its rule/chain engine.

## Indices

- {ref}`genindex`
- {ref}`modindex`
