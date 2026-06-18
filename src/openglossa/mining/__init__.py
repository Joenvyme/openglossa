"""Term mining from parallel data (P4).

Pipeline: statistical extraction (log-likelihood, c-value) + phrase tables
(fast_align/eflomal) + embedding alignment (LaBSE/simalign) → candidate term
pairs absent from TERMDAT → LLM ``verify`` against source → human review queue.

Stubs for now.
"""

from __future__ import annotations

__all__ = ["extract_candidates", "verify"]


def extract_candidates(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("Term candidate extraction (P4) is not implemented yet.")


def verify(*args, **kwargs):  # noqa: ANN002, ANN003
    """Verify a candidate term pair against official source evidence.

    Must never fabricate (hard rule #4): return supported=False when no source
    supports the pair.
    """
    raise NotImplementedError("LLM source verification (P4) is not implemented yet.")
