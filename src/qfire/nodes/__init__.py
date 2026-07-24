"""DetectorNode base contract: every node type returns a NodeVerdict."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

Verdict = Literal["block", "allow", "abstain"]


@dataclass(frozen=True, slots=True)
class NodeVerdict:
    verdict: Verdict
    confidence: float | None = None
    rationale: str | None = None
    latency_ms: float = 0.0


class DetectorNode(Protocol):
    """A single pipeline step. `type` matches the YAML `type` field."""

    type: str

    def run(self, prompt: str) -> NodeVerdict: ...


# Registry populated by each node module at import time.
NODE_TYPES: dict[str, type] = {}


def register(type_name: str):
    def _decorator(cls):
        NODE_TYPES[type_name] = cls
        return cls

    return _decorator
