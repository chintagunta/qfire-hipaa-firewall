from qfire import validate_rule
from qfire.rules import ExemplarSet, Rule, RuleNode


def test_validate_rule_reports_pass_and_fail():
    rule = Rule(
        id="test_rule",
        scope="test scope",
        pipeline=(RuleNode(type="pattern", config={"deny": [r"forbidden"]}),),
        exemplars=ExemplarSet(
            in_scope=("this is fine", "forbidden word here"),  # second one should fail
            out_of_scope=("forbidden word here", "this is fine"),  # second one should fail
        ),
    )
    result = validate_rule(rule)
    assert "this is fine" in result.passed
    assert "forbidden word here" in result.passed
    assert any(p == "forbidden word here" for p, _ in result.failed)
    assert any(p == "this is fine" for p, _ in result.failed)
