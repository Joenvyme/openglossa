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


def _oriented(tu: TranslationUnit, src_lang: str, tgt_lang: str) -> tuple[str, str] | None:
    """Return ``(src, tgt)`` text oriented to the requested direction, or None."""
    if str(tu.src_lang) == src_lang and str(tu.tgt_lang) == tgt_lang:
        return tu.src, tu.tgt
    if str(tu.src_lang) == tgt_lang and str(tu.tgt_lang) == src_lang:
        return tu.tgt, tu.src
    return None


def search_parallel(
    repo: Repository,
    text: str,
    src_lang: str,
    tgt_lang: str,
    k: int = 5,
    *,
    index: Any = None,
) -> dict[str, Any]:
    """RAG over the TM (few-shot examples), with citations.

    Direction-agnostic: TUs stored in either orientation are matched. When a
    sqlite-vec ``index`` (LaBSE/embeddings) is provided it is used for semantic
    retrieval, with a transparent fallback to the deterministic lexical baseline.
    """
    if index is not None:
        try:
            hits = index.search(text, src_lang, tgt_lang, k)
            return {"results": hits, "method": "vector", "disclaimer": DISCLAIMER}
        except Exception as exc:  # noqa: BLE001 - degrade gracefully to lexical
            return _search_parallel_lexical(repo, text, src_lang, tgt_lang, k, error=str(exc))
    return _search_parallel_lexical(repo, text, src_lang, tgt_lang, k)


def _search_parallel_lexical(
    repo: Repository,
    text: str,
    src_lang: str,
    tgt_lang: str,
    k: int = 5,
    *,
    error: str | None = None,
) -> dict[str, Any]:
    q = text.strip().casefold()
    scored: list[tuple[float, str, str, TranslationUnit]] = []
    for tu in repo.tus:
        oriented = _oriented(tu, src_lang, tgt_lang)
        if oriented is None:
            continue
        src_text, tgt_text = oriented
        score = _overlap(q, src_text.casefold())
        if score > 0:
            scored.append((score, src_text, tgt_text, tu))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    hits = [
        {
            "src": src_text,
            "tgt": tgt_text,
            "source": {"name": tu.source.name, "ref": tu.source.ref, "uri": str(tu.source.uri)},
            "score": round(score, 4),
        }
        for score, src_text, tgt_text, tu in scored[:k]
    ]
    out: dict[str, Any] = {"results": hits, "method": "lexical", "disclaimer": DISCLAIMER}
    if error:
        out["vector_error"] = error
    return out


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

    # Also accept attestation in the official parallel TM (both terms co-occur
    # in the same aligned segment), which is genuine source evidence.
    for tu in repo.tus:
        oriented = _oriented(tu, src_lang, tgt_lang)
        if oriented is None:
            continue
        src_text, tgt_text = oriented
        if s in src_text.casefold() and t in tgt_text.casefold():
            evidence.append(
                {
                    "name": tu.source.name,
                    "uri": str(tu.source.uri),
                    "license": tu.source.license,
                    "ref": tu.source.ref,
                }
            )
            if len(evidence) >= 5:
                break
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
    """Fetch the official Fedlex text for an ELI/citation (live, best-effort)."""
    try:
        from openglossa.sources import fedlex

        result = fedlex.fetch_official_text(eli_or_citation, lang)
    except Exception as exc:  # noqa: BLE001 - live source is best-effort
        result = {"text": None, "uri": None, "lang": lang, "error": str(exc)}
    result["disclaimer"] = DISCLAIMER
    return result


def suggest_glossary(
    repo: Repository,
    text: str,
    src_lang: str,
    tgt_lang: str,
    *,
    max_terms: int = 50,
) -> dict[str, Any]:
    """Stretch tool: extract known terms occurring in a passage + official trads.

    Scans the local termbase for source-language terms present in ``text`` and
    returns their official translation with citations. Deterministic and offline.
    """
    hay = text.casefold()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rec in repo.terms:
        res = _term_record_to_result(rec, src_lang, tgt_lang)
        if not res:
            continue
        for term in rec.terms.get(src_lang) or []:
            key = term.text.casefold()
            if key in seen or key not in hay:
                continue
            seen.add(key)
            out.append(
                {
                    "term": term.text,
                    "translation": res["translations"][0],
                    "sources": res["sources"],
                }
            )
            if len(out) >= max_terms:
                return {"results": out, "disclaimer": DISCLAIMER}
    return {"results": out, "disclaimer": DISCLAIMER}


def _overlap(query: str, text: str) -> float:
    qa = set(query.split())
    ta = set(text.split())
    if not qa or not ta:
        return 0.0
    return len(qa & ta) / len(qa)


# --------------------------------------------------------------------------- #
# MCP wiring (Streamable HTTP)
# --------------------------------------------------------------------------- #


DEFAULT_INDEX_PATH = Path(os.environ.get("OPENGLOSSA_INDEX", "data/processed/tm_index.db"))


def _maybe_open_index(index_path: Path | None) -> Any:
    """Open a sqlite-vec index with the LaBSE encoder, or return None."""
    if index_path is None or not Path(index_path).exists():
        return None
    try:
        from openglossa.search import VectorIndex, load_labse

        return VectorIndex.open(index_path, load_labse())
    except Exception:  # noqa: BLE001 - missing extra/model -> lexical fallback
        return None


def build_server(
    repo: Repository | None = None,
    *,
    termdat_live: bool = True,
    index: Any = None,
    index_path: Path | None = DEFAULT_INDEX_PATH,
    stateless: bool = False,
):
    """Build a FastMCP server bound to ``repo`` (loaded from disk if None).

    ``termdat_live`` enables the live TERMDAT backbone for ``lookup_term``.
    ``index`` (or an ``index_path`` to open) enables semantic ``search_parallel``;
    without it, ``search_parallel`` uses the lexical baseline.
    ``stateless`` runs the Streamable HTTP transport without persistent sessions
    and with JSON responses — required for serverless hosts (e.g. Vercel) where
    each request is a fresh, isolated function invocation.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "The MCP server requires the 'mcp' extra: pip install 'openglossa[mcp]'"
        ) from exc

    repo = repo or Repository.load()
    if index is None:
        index = _maybe_open_index(index_path)

    # On serverless hosts the platform proxy terminates TLS and sets the public
    # Host header (e.g. *.vercel.app, a custom domain), which the SDK's default
    # DNS-rebinding protection would reject ("Invalid Host header"). Disable it
    # for the hosted, stateless transport — the tools are public and read-only.
    transport_security = None
    if stateless:
        from mcp.server.transport_security import TransportSecuritySettings

        transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

    mcp = FastMCP(
        "OpenGlossa",
        stateless_http=stateless,
        json_response=stateless,
        transport_security=transport_security,
    )

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
        return search_parallel(repo, text, src_lang, tgt_lang, k, index=index)

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

    @mcp.tool()
    def suggest_glossary_tool(
        text: str, src_lang: str, tgt_lang: str
    ) -> dict[str, Any]:
        """Extract known legal terms from a passage with their official translations."""
        return suggest_glossary(repo, text, src_lang, tgt_lang)

    return mcp


def main() -> None:
    server = build_server()
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
