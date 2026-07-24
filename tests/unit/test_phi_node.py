from qfire.nodes.phi import PhiNode


def test_flags_synthetic_identifier_with_category():
    node = PhiNode()
    result = node.run("Patient MRN: 5551234 needs a callback.")
    assert result.verdict == "block"
    assert result.rationale.startswith("phi:")


def test_no_match_on_clean_prompt():
    node = PhiNode()
    result = node.run("How do I book a physical therapy appointment for next week?")
    assert result.verdict == "abstain"


def test_ssn_pattern_detected():
    node = PhiNode()
    result = node.run("His SSN is 123-45-6789.")
    assert result.verdict == "block"
    assert result.rationale == "phi:ssn"
