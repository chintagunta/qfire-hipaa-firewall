"""LLM scope-judge detector node: stdlib `urllib.request` only, per research.md (avoids an
extra HTTP-client dependency for this single, optional, low-frequency node type).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from qfire.nodes import NodeVerdict, register


@register("judge")
class JudgeNode:
    type = "judge"

    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/generate",
        scope: str = "",
        timeout: float = 5.0,
        **_ignored,
    ):
        self._endpoint = endpoint
        self._scope = scope
        self._timeout = timeout

    def run(self, prompt: str) -> NodeVerdict:
        payload = json.dumps(
            {
                "prompt": f"Scope: {self._scope}\nRequest: {prompt}\nIs this request in scope? Answer allow or block.",
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self._endpoint, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            # Fail-closed is enforced by the caller (evaluate_rule -> DetectorError); an
            # unreachable judge must not silently allow a scope decision through.
            raise RuntimeError(f"judge endpoint unreachable: {exc}") from exc

        answer = str(body.get("response", "")).strip().lower()
        verdict = "block" if "block" in answer else "allow"
        return NodeVerdict(verdict=verdict, rationale=f"judge response: {answer!r}")
