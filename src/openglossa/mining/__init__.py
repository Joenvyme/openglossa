"""Term mining from parallel data (P4).

Baseline pipeline (deterministic, dependency-free): statistical n-gram
extraction → cross-lingual pairing by co-occurrence (Dice) → ``verify`` against
official source segments → human review queue. Heavy aligners (eflomal,
fast_align) and embedding aligners (LaBSE/simalign) remain optional backends.
"""

from __future__ import annotations

from .extract import STOPWORDS, candidate_terms, mine_pairs, verify

# Backwards-compatible alias used elsewhere in the brief.
extract_candidates = candidate_terms

__all__ = [
    "STOPWORDS",
    "candidate_terms",
    "extract_candidates",
    "mine_pairs",
    "verify",
]
