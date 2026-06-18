"""Alignment strategies.

* ``eli-structural`` — pair Fedlex articles/alinéas across languages by ELI/eId
  structure (implemented in :mod:`openglossa.align.eli_structural`).
* ``labse`` — embedding-based alignment (LaBSE via sentence-transformers) for
  segments without a shared structural key (P4 stub).
"""

from __future__ import annotations

from openglossa.align.eli_structural import align_segments, shared_eids

__all__ = ["align_segments", "shared_eids", "labse"]


def labse(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("LaBSE alignment (P4) is not implemented yet.")
