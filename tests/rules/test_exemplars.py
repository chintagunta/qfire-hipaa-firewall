"""Every shipped rule's own exemplars are exercised as automated tests (constitution III)."""

import pytest

from qfire import load_rules, validate_rule

_RULES = load_rules("rules/")


@pytest.mark.parametrize("rule", list(_RULES), ids=lambda r: r.id)
def test_rule_exemplars_all_pass(rule):
    result = validate_rule(rule)
    assert not result.failed, f"rule {rule.id} failed exemplars: {result.failed}"
