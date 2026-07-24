# Detector nodes

Every pipeline entry in a rule's YAML has a `type` matching one of these registered node
classes, plus `config` keys passed as constructor kwargs. `qfire.nodes.NODE_TYPES` is the
`{type_name: class}` registry that `register()` populates below, at import time.

```{eval-rst}
.. module:: qfire.nodes

.. autofunction:: register
.. autoclass:: DetectorNode
   :members:
.. autoclass:: NodeVerdict
   :members:
```

## `pattern`

Cheapest-first deny/allow-list regex matching. `deny` patterns block on match; `allow`
patterns allow; otherwise the node abstains.

```{eval-rst}
.. autoclass:: qfire.nodes.pattern.PatternNode
   :members:
```

## `phi`

HIPAA Safe-Harbor identifier panel — 16 of the 18 identifier categories are pattern-matched
(biometric identifiers and full-face photos are not text-detectable and are intentionally
excluded).

```{eval-rst}
.. autoclass:: qfire.nodes.phi.PhiNode
   :members:
```

## `classifier`

Local injection classifier: onnxruntime + tokenizers when a `model_path` is configured and
those optional dependencies are installed; otherwise degrades to a lexical fallback, always
reported in the verdict rationale.

```{eval-rst}
.. autoclass:: qfire.nodes.classifier.ClassifierNode
   :members:
```

## `judge`

LLM scope-judge over HTTP (stdlib `urllib` only), e.g. a local Ollama `endpoint`. Raises on
an unreachable endpoint rather than silently allowing — fail-closed is enforced by the
caller.

```{eval-rst}
.. autoclass:: qfire.nodes.judge.JudgeNode
   :members:
```
