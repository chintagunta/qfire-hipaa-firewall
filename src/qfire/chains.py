"""Chain dataclass, YAML load/validate, and the evaluation engine (ordered + expression modes).

Cheap-before-expensive short-circuit and fail-closed semantics per constitution IV/V.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from qfire.errors import ChainValidationError
from qfire.nodes import NODE_TYPES, NodeVerdict
from qfire.rules import Rule, RuleSet
from qfire.trace import DecisionTrace, NodeResult

VALID_MODES = {"ordered", "expression"}
VALID_DEFAULTS = {"allow", "block"}
VALID_FAIL_POLICIES = {"fail_closed", "fail_open"}


@dataclass(frozen=True, slots=True)
class Chain:
    id: str
    mode: str
    default: str | None = None
    rules: tuple[str, ...] = ()
    groups: dict[str, str] = field(default_factory=dict)
    expression: str | None = None
    fail_policy: str = "fail_closed"


def _parse_chain(doc: dict, file: str, rules: RuleSet) -> Chain:
    chain_id = doc.get("id")
    if not chain_id:
        raise ChainValidationError(file, "id", "required field missing")
    mode = doc.get("mode")
    if mode not in VALID_MODES:
        raise ChainValidationError(file, "mode", f"must be one of {VALID_MODES}")

    fail_policy = doc.get("fail_policy", "fail_closed")
    if fail_policy not in VALID_FAIL_POLICIES:
        raise ChainValidationError(file, "fail_policy", f"must be one of {VALID_FAIL_POLICIES}")

    if mode == "ordered":
        rule_ids = doc.get("rules")
        default = doc.get("default")
        if not rule_ids:
            raise ChainValidationError(file, "rules", "required for ordered mode")
        if default not in VALID_DEFAULTS:
            raise ChainValidationError(file, "default", f"must be one of {VALID_DEFAULTS}")
        for rid in rule_ids:
            if rid not in rules:
                raise ChainValidationError(file, "rules", f"unknown rule id {rid!r}")
        return Chain(
            id=str(chain_id),
            mode=mode,
            default=default,
            rules=tuple(rule_ids),
            fail_policy=fail_policy,
        )

    # expression mode
    expression = doc.get("expression")
    if not expression:
        raise ChainValidationError(file, "expression", "required for expression mode")
    groups = doc.get("groups") or {}
    referenced_ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression))
    for group_expr in groups.values():
        referenced_ids |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", group_expr))
    referenced_ids -= {"AND", "OR", "NOT"} | set(groups)
    for rid in referenced_ids:
        if rid not in rules:
            raise ChainValidationError(file, "expression", f"unknown rule id {rid!r}")
    return Chain(
        id=str(chain_id),
        mode=mode,
        groups=dict(groups),
        expression=str(expression),
        fail_policy=fail_policy,
    )


class ChainSet:
    def __init__(self, chains: dict[str, Chain], rules: RuleSet):
        self._chains = chains
        self.rules = rules

    def __getitem__(self, chain_id: str) -> Chain:
        return self._chains[chain_id]

    def __contains__(self, chain_id: str) -> bool:
        return chain_id in self._chains


def load_chains(path: str | Path, rules: RuleSet) -> ChainSet:
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.rglob("*.yaml")) + sorted(path.rglob("*.yml"))
    chains: dict[str, Chain] = {}
    for file in files:
        doc = yaml.safe_load(file.read_text()) or {}
        chain = _parse_chain(doc, str(file), rules)
        chains[chain.id] = chain
    return ChainSet(chains, rules)


class DetectorError(Exception):
    """Raised when a detector node cannot produce a verdict. Triggers fail-closed."""


def _build_node(node_type: str, config: dict):
    cls = NODE_TYPES.get(node_type)
    if cls is None:
        raise DetectorError(f"no detector implementation registered for type {node_type!r}")
    return cls(**config)


def evaluate_rule(rule: Rule, prompt: str) -> tuple[str, list[NodeResult]]:
    """Run rule.pipeline cheapest-first with short-circuit. Returns (verdict, node_results).

    The first node to return a determinate verdict ("block"/"allow", not "abstain") decides
    the rule's outcome. With short_circuit="stop_on_first_block" evaluation stops there;
    with "run_all" every remaining node still runs (for a complete audit trace) but the
    first determinate verdict still wins.
    """
    results: list[NodeResult] = []
    final_verdict: str | None = None
    for rule_node in rule.pipeline:
        node = _build_node(rule_node.type, rule_node.config)
        start = time.perf_counter()
        try:
            verdict: NodeVerdict = node.run(prompt)
        except Exception as exc:  # noqa: BLE001 - any detector failure triggers fail-closed
            raise DetectorError(f"rule {rule.id!r} node {rule_node.type!r} failed: {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000
        results.append(
            NodeResult(
                rule_id=rule.id,
                node_type=rule_node.type,
                verdict=verdict.verdict,
                confidence=verdict.confidence,
                rationale=verdict.rationale,
                latency_ms=latency_ms,
            )
        )
        if verdict.verdict in ("block", "allow") and final_verdict is None:
            final_verdict = verdict.verdict
            if rule.short_circuit == "stop_on_first_block":
                return final_verdict, results
    return final_verdict or "allow", results


def _rule_blocks(rule_id: str, ruleset: RuleSet, prompt: str, all_results: list[NodeResult]) -> bool:
    verdict, results = evaluate_rule(ruleset[rule_id], prompt)
    all_results.extend(results)
    return verdict == "block"


_TOKEN_RE = re.compile(r"\(|\)|AND|OR|NOT|[A-Za-z_][A-Za-z0-9_]*")


def _expand_groups(expression: str, groups: dict[str, str]) -> str:
    expanded = expression
    for _ in range(len(groups) + 1):
        changed = False
        for name, sub_expr in groups.items():
            pattern = re.compile(rf"\b{re.escape(name)}\b")
            if pattern.search(expanded):
                expanded = pattern.sub(f"({sub_expr})", expanded)
                changed = True
        if not changed:
            break
    return expanded


def _eval_boolean_expression(expression: str, resolve) -> bool:
    """Tiny recursive-descent parser for `AND`/`OR`/`NOT`/parens over identifier operands."""
    tokens = _TOKEN_RE.findall(expression)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def advance():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        return tok

    def parse_or():
        nonlocal pos
        left = parse_and()
        while peek() == "OR":
            advance()
            right = parse_and()
            left = left or right
        return left

    def parse_and():
        nonlocal pos
        left = parse_not()
        while peek() == "AND":
            advance()
            right = parse_not()
            left = left and right
        return left

    def parse_not():
        nonlocal pos
        if peek() == "NOT":
            advance()
            return not parse_not()
        return parse_atom()

    def parse_atom():
        nonlocal pos
        tok = peek()
        if tok == "(":
            advance()
            val = parse_or()
            if peek() != ")":
                raise DetectorError(f"malformed expression: {expression!r}")
            advance()
            return val
        if tok is None or tok in ("AND", "OR", "NOT", ")"):
            raise DetectorError(f"malformed expression: {expression!r}")
        advance()
        return resolve(tok)

    result = parse_or()
    if pos != len(tokens):
        raise DetectorError(f"malformed expression: {expression!r}")
    return result


def evaluate_chain(prompt: str, chain: Chain, rules: RuleSet) -> DecisionTrace:
    """Evaluate `prompt` against `chain`. Never raises: errors are captured fail-closed."""
    all_results: list[NodeResult] = []
    try:
        if chain.mode == "ordered":
            for rule_id in chain.rules:
                if _rule_blocks(rule_id, rules, prompt, all_results):
                    return DecisionTrace(
                        prompt_hash=_hash(prompt),
                        chain_id=chain.id,
                        decision="block",
                        node_results=tuple(all_results),
                        fired_rule_id=rule_id,
                    )
            return DecisionTrace(
                prompt_hash=_hash(prompt),
                chain_id=chain.id,
                decision=chain.default,
                node_results=tuple(all_results),
            )

        expanded = _expand_groups(chain.expression, chain.groups)

        def resolve(rule_id: str) -> bool:
            return _rule_blocks(rule_id, rules, prompt, all_results)

        blocked = _eval_boolean_expression(expanded, resolve)
        decision = "block" if blocked else "allow"
        fired = None
        if decision == "block":
            blocking = [r.rule_id for r in all_results if r.verdict == "block"]
            fired = blocking[-1] if blocking else None
        return DecisionTrace(
            prompt_hash=_hash(prompt),
            chain_id=chain.id,
            decision=decision,
            node_results=tuple(all_results),
            fired_rule_id=fired,
        )
    except Exception as exc:  # noqa: BLE001
        # fail_policy="fail_open" is accepted at load time but not honored here: constitution
        # Principle V mandates fail-closed on error, so any evaluation error blocks regardless.
        return DecisionTrace(
            prompt_hash=_hash(prompt),
            chain_id=chain.id,
            decision="block",
            node_results=tuple(all_results),
            error=str(exc),
        )


def _hash(prompt: str) -> str:
    from qfire.trace import hash_prompt

    return hash_prompt(prompt)
