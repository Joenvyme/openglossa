"""TERMDAT connector — official federal terminology database (~400K entries).

Status: 🟠 ORANGE. Free access, but **redistribution license is NOT confirmed**
(see LICENSING.md, hard rule #6). Therefore this connector is **live-only**: we
query at request time (e.g. from the MCP server) and must NOT bundle the raw
upstream text in downloadable dumps. Only ``concept_id`` + URI + derived
alignments may be persisted until the license is confirmed.

This is a P3 stub: the public query surface is defined, with a guard that makes
the live-only constraint explicit and a placeholder implementation.
"""

from __future__ import annotations

from openglossa.schemas import TermRecord

SOURCE_NAME = "TERMDAT"
# Until confirmed, this tag signals "do not redistribute raw text".
LICENSE_TAG = "OGD-open-use-UNCONFIRMED"
LINDAS_SPARQL = "https://lindas.admin.ch/query"

#: Hard rule #6 guard. Flip to True only once redistribution is confirmed in
#: LICENSING.md; the exporters check this before persisting raw upstream text.
REDISTRIBUTION_CONFIRMED = False


def lookup_live(
    query: str,
    *,
    src_lang: str,
    tgt_lang: str,
    domain: str | None = None,
    limit: int = 10,
) -> list[TermRecord]:
    """Live lookup against TERMDAT (LINDAS SPARQL / termdat API).

    Returns concept records with equivalents, domain and legal basis. Intended to
    be called by the MCP server at request time, never to populate a redistributable
    dump (hard rule #6).

    Raises
    ------
    NotImplementedError
        P3 not implemented yet.
    """
    raise NotImplementedError(
        "TERMDAT live lookup (P3) is not implemented yet. "
        "See LICENSING.md before persisting any raw upstream text."
    )


def assert_redistribution_allowed() -> None:
    """Raise unless TERMDAT redistribution has been confirmed (hard rule #6)."""
    if not REDISTRIBUTION_CONFIRMED:
        raise PermissionError(
            "TERMDAT redistribution is not confirmed (LICENSING.md). "
            "Live-only: do not bundle raw upstream text in dumps."
        )
