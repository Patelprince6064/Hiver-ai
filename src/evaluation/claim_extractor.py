"""Claim extraction from generated replies.

Extracts candidate claims using deterministic techniques.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from src.evaluation.fact_types import FactType, classify_fact_type


@dataclass
class Claim:
    """An extracted claim from a generated reply."""

    text: str
    fact_type: FactType
    start: int
    end: int
    confidence: float = 1.0


SENTENCE_SPLIT_RE = re.compile(r'[.!?\n]+')
CLAUSE_SPLIT_RE = re.compile(r'[,;]')


def extract_claims(reply_text: str) -> list[Claim]:
    """Extract candidate claims from a generated reply.

    Uses sentence and clause splitting to identify individual claims.

    Args:
        reply_text: The generated reply text.

    Returns:
        List of extracted Claim objects.
    """
    if not reply_text or not reply_text.strip():
        return []

    claims: list[Claim] = []

    sentences = _split_sentences(reply_text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if _is_greeting_only(sentence):
            continue

        if _is_meta_statement(sentence):
            continue

        clauses = _split_clauses(sentence)

        for clause in clauses:
            clause = clause.strip()
            if not clause or len(clause.split()) < 2:
                continue

            fact_type = classify_fact_type(clause)
            start = reply_text.find(clause)
            end = start + len(clause) if start >= 0 else len(reply_text)

            claims.append(Claim(
                text=clause,
                fact_type=fact_type,
                start=start,
                end=end,
                confidence=1.0,
            ))

    return claims


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    parts = SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _split_clauses(text: str) -> list[str]:
    """Split a sentence into clauses."""
    return CLAUSE_SPLIT_RE.split(text)


def _is_greeting_only(text: str) -> bool:
    """Check if text is just a greeting."""
    lower = text.lower().strip()
    greetings = {"hello", "hi", "hey", "dear customer", "dear user"}
    return lower in greetings


def _is_meta_statement(text: str) -> bool:
    """Check if text is a meta statement about the system."""
    lower = text.lower()
    meta_patterns = [
        "i am an ai",
        "i'm an ai",
        "as an ai",
        "i am a bot",
        "i'm a bot",
        "as a bot",
        "i cannot",
        "i can't",
        "i am unable",
    ]
    return any(p in lower for p in meta_patterns)
