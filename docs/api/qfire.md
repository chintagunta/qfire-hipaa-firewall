# qfire (public API)

```{eval-rst}
.. module:: qfire

.. autofunction:: evaluate
.. autofunction:: validate_rule
.. autofunction:: configure_audit_log

.. autoclass:: Decision
   :members:

.. autoclass:: ExemplarValidationResult
   :members:
```

## Rules

```{eval-rst}
.. autofunction:: qfire.rules.load_rules
.. autoclass:: qfire.rules.Rule
   :members:
.. autoclass:: qfire.rules.RuleNode
   :members:
.. autoclass:: qfire.rules.RuleSet
   :members:
.. autoclass:: qfire.rules.ExemplarSet
   :members:
```

## Chains

```{eval-rst}
.. autofunction:: qfire.chains.load_chains
.. autofunction:: qfire.chains.evaluate_chain
.. autofunction:: qfire.chains.evaluate_rule
.. autoclass:: qfire.chains.Chain
   :members:
.. autoclass:: qfire.chains.ChainSet
   :members:
```

## Trace / audit log

```{eval-rst}
.. autoclass:: qfire.trace.DecisionTrace
   :members:
.. autoclass:: qfire.trace.NodeResult
   :members:
.. autoclass:: qfire.trace.AuditLog
   :members:
.. autofunction:: qfire.trace.hash_prompt
```

## Normalization

```{eval-rst}
.. autofunction:: qfire.normalize.normalize
```
