"""Rule/ExemplarSet dataclasses + YAML load/validate. Policy is data, not code (constitution I)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from qfire.errors import RuleValidationError

VALID_SHORT_CIRCUIT = {"stop_on_first_block", "run_all"}
VALID_NODE_TYPES = {"pattern", "phi", "classifier", "judge"}


@dataclass(frozen=True, slots=True)
class ExemplarSet:
    in_scope: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RuleNode:
    """A single entry in a rule's detector pipeline (unvalidated shape, config only)."""

    type: str
    config: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    scope: str
    pipeline: tuple[RuleNode, ...]
    exemplars: ExemplarSet = field(default_factory=ExemplarSet)
    short_circuit: str = "stop_on_first_block"


def _require(doc: dict, key: str, file: str) -> object:
    if key not in doc or doc[key] in (None, "", []):
        raise RuleValidationError(file, key, "required field missing or empty")
    return doc[key]


def _parse_rule(doc: dict, file: str) -> Rule:
    rule_id = _require(doc, "id", file)
    scope = _require(doc, "scope", file)
    raw_pipeline = _require(doc, "pipeline", file)
    if not isinstance(raw_pipeline, list) or len(raw_pipeline) == 0:
        raise RuleValidationError(file, "pipeline", "must be a non-empty list")

    nodes = []
    for i, entry in enumerate(raw_pipeline):
        if not isinstance(entry, dict) or "type" not in entry:
            raise RuleValidationError(file, f"pipeline[{i}]", "missing 'type'")
        node_type = entry["type"]
        if node_type not in VALID_NODE_TYPES:
            raise RuleValidationError(
                file, f"pipeline[{i}].type", f"unknown detector type {node_type!r}"
            )
        config = {k: v for k, v in entry.items() if k != "type"}
        nodes.append(RuleNode(type=node_type, config=config))

    short_circuit = doc.get("short_circuit", "stop_on_first_block")
    if short_circuit not in VALID_SHORT_CIRCUIT:
        raise RuleValidationError(file, "short_circuit", f"must be one of {VALID_SHORT_CIRCUIT}")

    exemplars_doc = doc.get("exemplars") or {}
    exemplars = ExemplarSet(
        in_scope=tuple(exemplars_doc.get("in_scope") or ()),
        out_of_scope=tuple(exemplars_doc.get("out_of_scope") or ()),
    )
    if not exemplars.in_scope and not exemplars.out_of_scope:
        raise RuleValidationError(file, "exemplars", "must contain at least one example")

    return Rule(
        id=str(rule_id),
        scope=str(scope),
        pipeline=tuple(nodes),
        exemplars=exemplars,
        short_circuit=short_circuit,
    )


class RuleSet:
    def __init__(self, rules: dict[str, Rule]):
        self._rules = rules

    def __getitem__(self, rule_id: str) -> Rule:
        return self._rules[rule_id]

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def __iter__(self):
        return iter(self._rules.values())

    def __len__(self) -> int:
        return len(self._rules)


def load_rules(path: str | Path) -> RuleSet:
    """Load and validate every rule YAML file under `path` (file or directory)."""
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.rglob("*.yaml")) + sorted(path.rglob("*.yml"))

    rules: dict[str, Rule] = {}
    for file in files:
        doc = yaml.safe_load(file.read_text()) or {}
        rule = _parse_rule(doc, str(file))
        rules[rule.id] = rule
    return RuleSet(rules)
