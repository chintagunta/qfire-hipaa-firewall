"""De-obfuscation normalization pass (FR-007): strip zero-width chars, fold homoglyphs and
leetspeak to ASCII, decode Base64/hex/ROT13 runs, appending each recovered layer.
"""

from __future__ import annotations

import base64
import binascii
import codecs
import re
import unicodedata

_ZERO_WIDTH = dict.fromkeys(
    ord(c) for c in ("​", "‌", "‍", "﻿", "⁠")
)

# Common homoglyphs: Cyrillic/Greek lookalikes -> ASCII.
_HOMOGLYPHS = str.maketrans(
    {
        "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
        "А": "A", "Е": "E", "О": "O", "Р": "P", "С": "C", "Т": "T", "Н": "H",
        "α": "a", "ο": "o", "ρ": "p", "ν": "v",
    }
)

_LEETSPEAK = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})

_BASE64_RUN = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
_HEX_RUN = re.compile(r"(?:[0-9A-Fa-f]{2}){8,}")


def _strip_zero_width(text: str) -> str:
    return text.translate(_ZERO_WIDTH)


def _fold_homoglyphs(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return text.translate(_HOMOGLYPHS)


def _fold_leetspeak(text: str) -> str:
    return text.translate(_LEETSPEAK)


def _decode_base64_runs(text: str) -> list[str]:
    recovered = []
    for match in _BASE64_RUN.finditer(text):
        try:
            decoded = base64.b64decode(match.group(), validate=True).decode("utf-8", errors="strict")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        if decoded.isprintable():
            recovered.append(decoded)
    return recovered


def _decode_hex_runs(text: str) -> list[str]:
    recovered = []
    for match in _HEX_RUN.finditer(text):
        try:
            decoded = bytes.fromhex(match.group()).decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError):
            continue
        if decoded.isprintable():
            recovered.append(decoded)
    return recovered


def _decode_rot13(text: str) -> str:
    return codecs.decode(text, "rot_13")


def normalize(prompt: str) -> str:
    """Return prompt with obfuscation layers stripped/decoded and appended for detection."""
    layers = [prompt]

    stripped = _strip_zero_width(prompt)
    if stripped != prompt:
        layers.append(stripped)

    folded = _fold_homoglyphs(_fold_leetspeak(stripped))
    if folded != stripped:
        layers.append(folded)

    layers.extend(_decode_base64_runs(prompt))
    layers.extend(_decode_hex_runs(prompt))
    layers.append(_decode_rot13(stripped))

    # de-duplicate while preserving order
    seen: set[str] = set()
    unique_layers = []
    for layer in layers:
        if layer not in seen:
            seen.add(layer)
            unique_layers.append(layer)
    return "\n".join(unique_layers)
