"""Local injection classifier node: onnxruntime (CPU) + tokenizers, per research.md.

Degrades to a transparent lexical fallback classifier when no ONNX model is configured or
the optional `onnxruntime`/`tokenizers` dependencies are not installed — the degradation is
always reported in the verdict rationale, never silent (constitution Principle V).
"""

from __future__ import annotations

from qfire.nodes import NodeVerdict, register

_FALLBACK_SIGNALS = (
    "ignore all previous",
    "ignore the previous",
    "ignore above instructions",
    "disregard prior instructions",
    "you are now dan",
    "jailbreak",
    "system prompt",
    "reveal your instructions",
    "act as if you have no restrictions",
)


def _lexical_fallback_score(prompt: str) -> float:
    lowered = prompt.lower()
    hits = sum(1 for signal in _FALLBACK_SIGNALS if signal in lowered)
    return min(1.0, hits * 0.5)


@register("classifier")
class ClassifierNode:
    type = "classifier"

    def __init__(self, threshold: float = 0.5, model_path: str | None = None, **_ignored):
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        self._threshold = threshold
        self._session = None
        self._tokenizer = None
        self._degraded = True
        if model_path:
            self._try_load_onnx(model_path)

    def _try_load_onnx(self, model_path: str) -> None:
        try:
            import onnxruntime as ort  # noqa: F401 - optional dependency, per research.md
            from tokenizers import Tokenizer  # noqa: F401

            self._session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self._tokenizer = Tokenizer.from_file(model_path.replace(".onnx", "-tokenizer.json"))
            self._degraded = False
        except Exception:
            # Any failure (missing dependency, missing/invalid model file) falls back to the
            # lexical classifier below; this is reported via rationale, not swallowed.
            self._session = None
            self._tokenizer = None
            self._degraded = True

    def run(self, prompt: str) -> NodeVerdict:
        if self._degraded or self._session is None:
            score = _lexical_fallback_score(prompt)
            verdict = "block" if score >= self._threshold else "abstain"
            return NodeVerdict(
                verdict=verdict,
                confidence=score,
                rationale="degraded: lexical fallback classifier (ONNX model unavailable)",
            )

        encoded = self._tokenizer.encode(prompt)
        inputs = {"input_ids": [encoded.ids]}
        outputs = self._session.run(None, inputs)
        score = float(outputs[0][0][1])  # assume [benign, attack] softmax output
        verdict = "block" if score >= self._threshold else "abstain"
        return NodeVerdict(verdict=verdict, confidence=score, rationale="onnxruntime classifier")
