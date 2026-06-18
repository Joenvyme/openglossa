"""Alignment strategies.

* ``eli-structural`` — pair Fedlex articles across languages by ELI/eId structure.
* ``labse`` — embedding-based alignment (LaBSE via sentence-transformers) for
  segments without a shared structural key.

P1/P4 work. Stubs for now.
"""

from __future__ import annotations

__all__ = ["eli_structural", "labse"]


def eli_structural(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("ELI-structural alignment (P1) is not implemented yet.")


def labse(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("LaBSE alignment (P4) is not implemented yet.")
