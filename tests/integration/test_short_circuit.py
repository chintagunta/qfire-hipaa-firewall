from qfire.chains import evaluate_rule
from qfire.rules import ExemplarSet, Rule, RuleNode


def test_expensive_node_skipped_after_cheap_block():
    rule = Rule(
        id="short_circuit_rule",
        scope="test",
        pipeline=(
            RuleNode(type="pattern", config={"deny": [r"forbidden"]}),
            RuleNode(type="classifier", config={"threshold": 0.0, "model_path": "/does/not/exist.onnx"}),
        ),
        exemplars=ExemplarSet(out_of_scope=("forbidden text",)),
        short_circuit="stop_on_first_block",
    )
    verdict, results = evaluate_rule(rule, "forbidden text here")
    assert verdict == "block"
    # only the cheap pattern node ran; the classifier node never executed
    assert len(results) == 1
    assert results[0].node_type == "pattern"


def test_run_all_executes_every_node_even_after_block():
    rule = Rule(
        id="run_all_rule",
        scope="test",
        pipeline=(
            RuleNode(type="pattern", config={"deny": [r"forbidden"]}),
            RuleNode(type="pattern", config={"deny": [r"never matches this"]}),
        ),
        exemplars=ExemplarSet(out_of_scope=("forbidden text",)),
        short_circuit="run_all",
    )
    verdict, results = evaluate_rule(rule, "forbidden text here")
    assert verdict == "block"
    assert len(results) == 2
