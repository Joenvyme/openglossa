"""Source connectors. Each connector captures provenance (hard rule #3) and is
aware of the license status declared in LICENSING.md.

Connectors only depend on the optional ``sources`` extra. Importing this package
must not fail when those deps are absent; import the concrete connector lazily.
"""

from __future__ import annotations

__all__ = ["fedlex", "slds", "termdat", "jurivoc"]
