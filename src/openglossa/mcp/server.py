"""OpenGlossa MCP server (P6).

Implements the tool contracts from §7 of PROJECT.md. Backed by a lightweight
in-memory repository loaded from JSONL produced by the pipeline
(``data/processed/terms.jsonl`` and ``data/processed/tus.jsonl``). When no data
is present, tools return empty results with an explicit note rather than
fabricating (hard rule #4).

Run:  python -m openglossa.mcp.server     (Streamable HTTP)

The ``mcp`` dependency is optional: ``pip install 'openglossa[mcp]'``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from openglossa.schemas import TermRecord, TranslationUnit

DISCLAIMER = (
    "OpenGlossa output is NOT the authoritative legal text. Verify against the "
    "official source (Fedlex RS + article, or the cited ATF/BGE reference)."
)

DEFAULT_DATA_DIR = Path(os.environ.get("OPENGLOSSA_DATA", "data/processed"))


# --------------------------------------------------------------------------- #
# In-memory repository
# --------------------------------------------------------------------------- #


class Repository:
    """Loads TermRecords and TranslationUnits from JSONL (one record per line)."""

    def __init__(self) -> None:
        self.terms: list[TermRecord] = []
        self.tus: list[TranslationUnit] = []

    @classmethod
    def load(cls, data_dir: Path = DEFAULT_DATA_DIR) -> Repository:
        repo = cls()
        terms_path = data_dir / "terms.jsonl"
        tus_path = data_dir / "tus.jsonl"
        if terms_path.exists():
            repo.terms = [
                TermRecord.model_validate_json(line)
                for line in terms_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        if tus_path.exists():
            repo.tus = [
                TranslationUnit.model_validate_json(line)
                for line in tus_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        return repo


def _sources_payload(rec: TermRecord) -> list[dict[str, Any]]:
    return [
        {"name": s.name, "uri": str(s.uri), "license": s.license, "ref": s.ref}
        for s in rec.sources
    ]


def _term_record_to_result(
    rec: TermRecord, src_lang: str, tgt_lang: str
) -> dict[str, Any] | None:
    """Shape a TermRecord into a lookup_term result for a language direction."""
    src_terms = [t.text for t in (rec.terms.get(src_lang) or [])]
    translations = [t.text for t in (rec.terms.get(tgt_lang) or [])]
    if not src_terms or not translations:
        return None
    return {
        "term": rec.preferred(src_lang),
        "translations": translations,
        "domain": rec.domain,
        "authority": rec.authority,
        "definition": rec.definition.get(tgt_lang) or rec.definition.get(src_lang),
        "sources": _sources_payload(rec),
    }


# --------------------------------------------------------------------------- #
# Tool implementations (pure functions, unit-testable without the MCP runtime)
# --------------------------------------------------------------------------- #


def lookup_term(
    repo: Repository,
    query: str,
    src_lang: str,
    tgt_lang: str,
    domain: str | None = None,
    *,
    termdat_live: bool = False,
) -> dict[str, Any]:
    q = query.strip().casefold()
    results: list[dict[str, Any]] = []
    for rec in repo.terms:
        if domain and domain not in rec.domain:
            continue
        src_terms = rec.terms.get(src_lang) or []
        if not any(q == t.text.casefold() or q in t.text.casefold() for t in src_terms):
            continue
        res = _term_record_to_result(rec, src_lang, tgt_lang)
        if res:
            results.append(res)

    if termdat_live:
        try:
            from openglossa.sources import termdat

            for rec in termdat.lookup_live(query, src_lang):
                res = _term_record_to_result(rec, src_lang, tgt_lang)
                if res:
                    results.append(res)
        except Exception as exc:  # noqa: BLE001 - live backbone is best-effort
            return {"results": results, "disclaimer": DISCLAIMER, "termdat_error": str(exc)}

    return {"results": results, "disclaimer": DISCLAIMER}


def search_parallel(
    repo: Repository,
    text: str,
    src_lang: str,
    tgt_lang: str,
    k: int = 5,
) -> dict[str, Any]:
    """Naive lexical RAG over the TM. Replaced by a vector index in P5/P6."""
    q = text.strip().casefold()
    scored: list[tuple[float, TranslationUnit]] = []
    for tu in repo.tus:
        if str(tu.src_lang) != src_lang or str(tu.tgt_lang) != tgt_lang:
            continue
        score = _overlap(q, tu.src.casefold())
        if score > 0:
            scored.append((score, tu))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [
        {
            "src": tu.src,
            "tgt": tu.tgt,
            "source": {"name": tu.source.name, "ref": tu.source.ref, "uri": str(tu.source.uri)},
            "score": round(score, 4),
        }
        for score, tu in scored[:k]
    ]
    return {"results": hits, "disclaimer": DISCLAIMER}


def verify_translation(
    repo: Repository,
    src_term: str,
    tgt_term: str,
    src_lang: str,
    tgt_lang: str,
) -> dict[str, Any]:
    """Is this term pair supported by an official source? Never fabricate (#4)."""
    s = src_term.strip().casefold()
    t = tgt_term.strip().casefold()
    evidence: list[dict[str, Any]] = []
    for rec in repo.terms:
        src_match = any(s == x.text.casefold() for x in (rec.terms.get(src_lang) or []))
        tgt_match = any(t == x.text.casefold() for x in (rec.terms.get(tgt_lang) or []))
        if src_match and tgt_match:
            evidence.extend(_sources_payload(rec))
    supported = bool(evidence)
    return {
        "supported": supported,
        "evidence": evidence,
        "note": (
            "Pair attested in an official source."
            if supported
            else "No official source supports this pair in the current dataset."
        ),
        "disclaimer": DISCLAIMER,
    }


def get_official_text(eli_or_citation: str, lang: str) -> dict[str, Any]:
    """Delegate to Fedlex (P1 / Fedlex Connector). Stub for now."""
    return {
        "text": None,
        "uri": None,
        "lang": lang,
        "note": "get_official_text delegates to Fedlex (P1) — not wired yet.",
        "disclaimer": DISCLAIMER,
    }


def _overlap(query: str, text: str) -> float:
    qa = set(query.split())
    ta = set(text.split())
    if not qa or not ta:
        return 0.0
    return len(qa & ta) / len(qa)


# --------------------------------------------------------------------------- #
# MCP wiring (Streamable HTTP)
# --------------------------------------------------------------------------- #


def build_server(repo: Repository | None = None, *, termdat_live: bool = True):
    """Build a FastMCP server bound to ``repo`` (loaded from disk if None).

    ``termdat_live`` enables the live TERMDAT backbone for ``lookup_term``.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "The MCP server requires the 'mcp' extra: pip install 'openglossa[mcp]'"
        ) from exc

    repo = repo or Repository.load()
    mcp = FastMCP("OpenGlossa")

    @mcp.tool()
    def lookup_term_tool(
        query: str, src_lang: str, tgt_lang: str, domain: str | None = None
    ) -> dict[str, Any]:
        """Look up official translations of a legal term, with source citations."""
        return lookup_term(repo, query, src_lang, tgt_lang, domain, termdat_live=termdat_live)

    @mcp.tool()
    def search_parallel_tool(
        text: str, src_lang: str, tgt_lang: str, k: int = 5
    ) -> dict[str, Any]:
        """Retrieve parallel example segments (few-shot RAG) with citations."""
        return search_parallel(repo, text, src_lang, tgt_lang, k)

    @mcp.tool()
    def verify_translation_tool(
        src_term: str, tgt_term: str, src_lang: str, tgt_lang: str
    ) -> dict[str, Any]:
        """Check whether a term pair is supported by an official source."""
        return verify_translation(repo, src_term, tgt_term, src_lang, tgt_lang)

    @mcp.tool()
    def get_official_text_tool(eli_or_citation: str, lang: str) -> dict[str, Any]:
        """Fetch the official Fedlex text for an ELI/citation in a given language."""
        return get_official_text(eli_or_citation, lang)

    return mcp


def main() -> None:
    server = build_server()
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
