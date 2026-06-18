"""Semantic search backend for ``search_parallel`` (P6 backlog).

A pluggable :class:`~openglossa.search.vector.Encoder` (LaBSE in production, a
deterministic hashing encoder for tests/CI) feeds a sqlite-vec vector index over
the translation memory. ``search_parallel`` uses it when available and falls back
to the lexical baseline otherwise.
"""

from __future__ import annotations

from openglossa.search.vector import (
    Encoder,
    HashingEncoder,
    VectorIndex,
    load_labse,
)

__all__ = ["Encoder", "HashingEncoder", "VectorIndex", "load_labse"]
