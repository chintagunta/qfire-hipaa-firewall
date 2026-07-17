"""DecisionTrace/NodeResult + append-only JSON-lines audit log (constitution V)."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True, slots=True)
class NodeResult:
    rule_id: str
    node_type: str
    verdict: str
    confidence: float | None
    rationale: str | None
    latency_ms: float


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    prompt_hash: str
    chain_id: str
    decision: str
    node_results: tuple[NodeResult, ...] = ()
    fired_rule_id: str | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_dict(self) -> dict:
        return asdict(self)


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class AuditLog:
    """Append-only JSON-lines writer. One line per evaluation, never rewritten."""

    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path else None
        self._lock = threading.Lock()

    def write(self, trace: DecisionTrace) -> None:
        if self._path is None:
            return
        line = json.dumps(trace.as_dict(), default=str)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
