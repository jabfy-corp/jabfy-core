"""Sanitisation of external strings before they reach the model (MASTER_PLAN §2.5)."""

import re
import unicodedata
from typing import Any

MAX_FIELD_LENGTH = 200
MAX_MESSAGE_LENGTH = 4000

# Chat-template markers and Markdown fences that could close or reopen a prompt section.
_DELIMITERS = re.compile(
    r"<\|[^|<>]{0,64}\|>|\[/?INST\]|<</?SYS>>|</?s>|<\s*/?\s*(?:system|user|assistant)\s*>|```",
    re.IGNORECASE,
)
_WHITESPACE_CONTROLS = "\t\n\r"


def sanitize_text(value: str, max_length: int = MAX_FIELD_LENGTH, *, multiline: bool = False) -> str:
    """Drop control and invisible characters, strip prompt delimiters, bound the length.

    Single-line fields (names, labels, states) have their line breaks turned into spaces.
    """
    chars = []
    for char in value:
        if char in _WHITESPACE_CONTROLS:
            chars.append(char if multiline else " ")
        elif unicodedata.category(char) not in ("Cc", "Cf", "Co", "Cs"):
            chars.append(char)
    cleaned = "".join(chars)
    previous = None
    while previous != cleaned:
        previous, cleaned = cleaned, _DELIMITERS.sub("", cleaned)
    return cleaned[:max_length]


def sanitize_tree(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {sanitize_text(key) if isinstance(key, str) else key: sanitize_tree(child)
                for key, child in value.items()}
    if isinstance(value, list):
        return [sanitize_tree(child) for child in value]
    return value
