"""PHI detector node: HIPAA Safe-Harbor identifier panel (FR-008).

Covers all 18 identifier categories by name; 16 are pattern-detectable in text and are
matched below. Two categories — "biometric identifiers" (fingerprints, voiceprints) and
"full-face photographic images" — are not detectable from text alone and are intentionally
NOT matched by this node; this limitation is called out here per constitution's
"Additional Constraints" (partial coverage must be documented, not silently shipped).
"""

from __future__ import annotations

try:
    import regex as _re
except ImportError:  # pragma: no cover
    import re as _re

from qfire.nodes import NodeVerdict, register

# Category -> compiled pattern. Patterns are intentionally permissive (recall over precision)
# since this is a guardrail, not a de-identification tool.
_PATTERNS: dict[str, "_re.Pattern"] = {
    "ssn": _re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone_or_fax": _re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
    "email": _re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "date": _re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b"),
    "mrn": _re.compile(r"\bMRN\s*[:#]?\s*\d{4,}\b", _re.IGNORECASE),
    "health_plan_beneficiary": _re.compile(r"\bbeneficiary\s*(?:id|number|#)?\s*[:#]?\s*\w{4,}\b", _re.IGNORECASE),
    "account_number": _re.compile(r"\baccount\s*(?:number|#)?\s*[:#]?\s*\d{4,}\b", _re.IGNORECASE),
    "certificate_or_license": _re.compile(r"\b(?:license|certificate)\s*(?:number|#)?\s*[:#]?\s*\w{4,}\b", _re.IGNORECASE),
    "vehicle_identifier": _re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b"),
    "device_identifier": _re.compile(r"\bdevice\s*(?:serial|id)\s*[:#]?\s*\w{4,}\b", _re.IGNORECASE),
    "url": _re.compile(r"\bhttps?://[^\s]+\b"),
    "ip_address": _re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "geographic_subdivision": _re.compile(r"\b\d{5}(?:-\d{4})?\b"),  # ZIP code
    "name": _re.compile(r"\bpatient\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"),
    "age_over_89": _re.compile(r"\bage[d]?\s*(?:9[0-9]|1\d{2})\b", _re.IGNORECASE),
    "other_unique_identifier": _re.compile(r"\b[A-Z]{2,4}-?\d{6,}\b"),
}


@register("phi")
class PhiNode:
    type = "phi"

    def __init__(self, categories: list[str] | None = None, **_ignored):
        selected = categories or list(_PATTERNS)
        self._patterns = {cat: _PATTERNS[cat] for cat in selected if cat in _PATTERNS}

    def run(self, prompt: str) -> NodeVerdict:
        for category, pattern in self._patterns.items():
            if pattern.search(prompt):
                return NodeVerdict(
                    verdict="block",
                    confidence=1.0,
                    rationale=f"phi:{category}",
                )
        return NodeVerdict(verdict="abstain")
