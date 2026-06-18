"""OpenGlossa — open Swiss legal termbase & translation memory, grounded in
official sources and exposed via MCP.

See PROJECT.md for the full project brief and LICENSING.md for the per-source
license registry. Hard rules (non-negotiable) are enforced throughout the
pipeline: provenance per record, no fabrication, official-source citation.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Supported language codes (ISO 639-1). RM/EN are stretch goals.
LANGUAGES = ("de", "fr", "it", "rm", "en")
CORE_LANGUAGES = ("de", "fr", "it")

__all__ = ["__version__", "LANGUAGES", "CORE_LANGUAGES"]
