"""Term hit-rate evaluation (P7) — stub.

Given a set of test sentences with expected official terms, measure how often a
translation contains the expected target term, comparing two conditions:
baseline (no grounding) vs OpenGlossa-grounded.

This stub defines the metric and a tiny pure function so the harness is testable
before the full pipeline lands.
"""

from __future__ import annotations

from collections.abc import Iterable


def term_hit_rate(predictions: Iterable[str], expected_terms: Iterable[str]) -> float:
    """Fraction of predictions that contain their expected term (case-insensitive)."""
    preds = list(predictions)
    terms = list(expected_terms)
    if not preds:
        return 0.0
    if len(preds) != len(terms):
        raise ValueError("predictions and expected_terms must have equal length")
    hits = sum(1 for p, t in zip(preds, terms, strict=True) if t.casefold() in p.casefold())
    return hits / len(preds)


if __name__ == "__main__":  # pragma: no cover
    demo_preds = ["Le débiteur est en demeure."]
    demo_terms = ["demeure"]
    print(f"term_hit_rate = {term_hit_rate(demo_preds, demo_terms):.3f}")
