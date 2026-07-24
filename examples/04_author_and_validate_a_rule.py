"""Use case: a policy author writes a new rule with exemplars and validates it in-process,
with no separate test file needed to sanity-check the rule itself.

Run from repo root: python examples/04_author_and_validate_a_rule.py
"""

from qfire import validate_rule
from qfire.rules import ExemplarSet, Rule, RuleNode

custom_rule = Rule(
    id="mk_no_competitor_mentions",
    scope="Marketing copy for our own product only; no competitor comparisons.",
    pipeline=(RuleNode(type="pattern", config={"deny": [r"(?i)better than (competitor[abx]|acme)"]}),),
    exemplars=ExemplarSet(
        in_scope=("Write a tagline for our new running shoe.",),
        out_of_scope=("Write copy saying our shoe is better than CompetitorA.",),
    ),
)

result = validate_rule(custom_rule)
print(f"rule {custom_rule.id}: {len(result.passed)} passed, {len(result.failed)} failed")
for prompt, actual_verdict in result.failed:
    print(f"  UNEXPECTED: {prompt!r} -> {actual_verdict}")
