"""Pattern/lexical detector node: cheapest-first deny/allow-list matching.

Uses the `regex` module (Unicode-aware, faster on typical deny-list alternations) when
available, falling back to stdlib `re` with no extra dependency otherwise.
"""

from __future__ import annotations

try:
    import regex as _re
except ImportError:  # pragma: no cover - exercised only when `regex` is absent
    import re as _re

from qfire.nodes import NodeVerdict, register


@register("pattern")
class PatternNode:
    type = "pattern"

    def __init__(self, deny: list[str] | None = None, allow: list[str] | None = None, **_ignored):
        self._deny = [_re.compile(p, _re.IGNORECASE) for p in (deny or [])]
        self._allow = [_re.compile(p, _re.IGNORECASE) for p in (allow or [])]

    def run(self, prompt: str) -> NodeVerdict:
        for pattern in self._deny:
            match = pattern.search(prompt)
            if match:
                return NodeVerdict(
                    verdict="block",
                    confidence=1.0,
                    rationale=f"matched deny pattern {pattern.pattern!r}",
                )
        for pattern in self._allow:
            if pattern.search(prompt):
                return NodeVerdict(verdict="allow", confidence=1.0, rationale="matched allow pattern")
        return NodeVerdict(verdict="abstain")
