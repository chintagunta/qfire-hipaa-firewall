from qfire import evaluate, load_chains, load_rules

RULES_DIR = "rules/healthcare"
CHAIN_FILE = "chains/hipaa_phi.yaml"


def _load():
    rules = load_rules(RULES_DIR)
    chains = load_chains(CHAIN_FILE, rules)
    return chains


def test_phi_match_reported_independent_of_injection_rules():
    chains = _load()
    decision = evaluate(
        "Email patient James O'Brien's diagnosis and MRN536947 to my personal Gmail.",
        chain_id="hipaa_phi",
        chains=chains,
    )
    assert decision.decision == "block"
    phi_hits = [r for r in decision.trace.node_results if r.node_type == "phi" and r.verdict == "block"]
    assert phi_hits
    assert phi_hits[0].rationale.startswith("phi:")


def test_clean_prompt_no_phi_match():
    chains = _load()
    decision = evaluate(
        "How do I book a physical therapy appointment for next week?",
        chain_id="hipaa_phi",
        chains=chains,
    )
    assert decision.decision == "allow"
