"""OpenGlossa MCP server package (P6).

Exposes lookup/search/verify tools over Streamable HTTP so the dataset can be
added as a custom connector in Claude.ai / Claude Desktop. Every response
includes source citations (the differentiator) and never fabricates a translation
(hard rule #4).
"""

from __future__ import annotations

__all__ = ["server"]
