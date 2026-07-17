"""qfire: declarative, positive-security prompt firewall — Python port.

Public API: load_rules, load_chains, evaluate, validate_rule.
See specs/001-qfire-python-port/contracts/public-api.md for the full contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from qfire.chains import Chain, ChainSet, evaluate_chain, evaluate_rule, load_chains
from qfire.errors import ChainValidationError, QfireError, RuleValidationError
from qfire.normalize import normalize
from qfire.rules import Rule, RuleSet, load_rules
from qfire.trace import AuditLog, DecisionTrace

# Import node modules for their @register("...") side effect, populating NODE_TYPES.
from qfire.nodes import classifier as _classifier  # noqa: F401,E402
from qfire.nodes import judge as _judge  # noqa: F401,E402
from qfire.nodes import pattern as _pattern  # noqa: F401,E402
from qfire.nodes import phi as _phi  # noqa: F401,E402

__all__ = [
    "Chain",
    "ChainSet",
    "ChainValidationError",
    "Decision",
    "ExemplarValidationResult",
    "QfireError",
    "Rule",
    "RuleSet",
    "RuleValidationError",
    "evaluate",
    "load_chains",
    "load_rules",
    "validate_rule",
]

_audit_log = AuditLog()


def configure_audit_log(path: str | None) -> None:
    """Set (or clear, with None) the file that evaluate() appends DecisionTrace records to."""
    global _audit_log
    _audit_log = AuditLog(path)


@dataclass(frozen=True, slots=True)
class Decision:
    decision: Literal["allow", "block"]
    fired_rule_id: str | None
    trace: DecisionTrace


def evaluate(prompt: str, chain_id: str, chains: ChainSet, *, normalize: bool = True) -> Decision:
    """Evaluate `prompt` against the named chain. Never raises for detector-level failures
    (fail-closed instead, per FR-010); raises KeyError only for an unknown chain_id."""
    chain = chains[chain_id]

    trace = evaluate_chain(prompt, chain, chains.rules)

    if normalize and trace.decision == "allow" and trace.error is None:
        normalized_prompt = _normalize_text(prompt)
        if normalized_prompt != prompt:
            normalized_trace = evaluate_chain(normalized_prompt, chain, chains.rules)
            if normalized_trace.decision == "block":
                trace = normalized_trace

    _audit_log.write(trace)
    return Decision(decision=trace.decision, fired_rule_id=trace.fired_rule_id, trace=trace)


def _normalize_text(prompt: str) -> str:
    return normalize(prompt)


@dataclass(frozen=True, slots=True)
class ExemplarValidationResult:
    rule_id: str
    passed: tuple[str, ...]
    failed: tuple[tuple[str, str], ...]


def validate_rule(rule: Rule) -> ExemplarValidationResult:
    """Evaluate every exemplar in `rule.exemplars` against `rule` alone (FR-006, Story 2)."""
    passed: list[str] = []
    failed: list[tuple[str, str]] = []
    for prompt in rule.exemplars.in_scope:
        verdict, _ = evaluate_rule(rule, prompt)
        if verdict == "block":
            failed.append((prompt, verdict))
        else:
            passed.append(prompt)
    for prompt in rule.exemplars.out_of_scope:
        verdict, _ = evaluate_rule(rule, prompt)
        if verdict == "block":
            passed.append(prompt)
        else:
            failed.append((prompt, verdict))
    return ExemplarValidationResult(rule_id=rule.id, passed=tuple(passed), failed=tuple(failed))
