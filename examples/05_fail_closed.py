"""Use case: a broken detector node never fails open — the request is blocked and the
error is visible in the decision trace, never silently swallowed.

Run from repo root: python examples/05_fail_closed.py
"""

from qfire import evaluate, load_chains, load_rules

rules = load_rules("tests/fixtures/broken_rules/")
chains = load_chains("tests/fixtures/broken_chains/", rules)

decision = evaluate("anything", chain_id="broken_chain", chains=chains)
print("decision:", decision.decision)
print("error:", decision.trace.error)
