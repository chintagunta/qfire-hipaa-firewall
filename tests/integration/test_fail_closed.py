from qfire import evaluate, load_chains, load_rules


def test_broken_detector_node_fails_closed():
    rules = load_rules("tests/fixtures/broken_rules/")
    chains = load_chains("tests/fixtures/broken_chains/", rules)

    decision = evaluate("anything", chain_id="broken_chain", chains=chains)

    assert decision.decision == "block"
    assert decision.trace.error is not None
