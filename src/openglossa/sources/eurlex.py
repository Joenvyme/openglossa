"""EUR-Lex / CELLAR connector — EU legislation parallel texts (live SPARQL).

Status: ✅ GREEN. Editorial content and metadata are reusable under CC-BY 4.0
(EU legal notice); legislative acts under Decision 2011/833/EU with attribution
(see LICENSING.md). Queries use the public CELLAR SPARQL endpoint — no API key.

This connector complements Swiss sources (Fedlex/SLDS): it provides **official EU
law** in EN/DE/FR/IT, not Swiss federal law. v1 retrieves parallel titles and
legislative summaries (``legissum`` abstracts) via SPARQL; full act body text
remains a future ingestion target (DGT-TM / CELLAR bulk).
"""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
SOURCE_NAME = "EUR-Lex"
LICENSE_TAG = "CC-BY-4.0-EU"
ATTRIBUTION = "© European Union — EUR-Lex (https://eur-lex.europa.eu)"
REDISTRIBUTION_CONFIRMED = True

# OpenGlossa lang code -> CELLAR ISO 639-3 authority code
LANG_TO_ISO3: dict[str, str] = {
    "de": "DEU",
    "fr": "FRA",
    "it": "ITA",
    "en": "ENG",
}
SUPPORTED_LANGS = tuple(LANG_TO_ISO3.keys())

_LANG_URI = "http://publications.europa.eu/resource/authority/language/{iso3}"
_TAG_RE = re.compile(r"<[^>]+>")


def assert_redistribution_allowed() -> None:
    """EUR-Lex/CELLAR reuse is permitted with attribution (CC-BY 4.0 / 2011/833)."""
    if not REDISTRIBUTION_CONFIRMED:
        raise PermissionError("EUR-Lex redistribution flag is disabled.")


def _lang_uri(lang: str) -> str:
    iso3 = LANG_TO_ISO3.get(lang)
    if iso3 is None:
        raise ValueError(f"Unsupported language for EUR-Lex: {lang}")
    return _LANG_URI.format(iso3=iso3)


def _clean_literal(value: str) -> str:
    """Strip XML/HTML markup from CELLAR XMLLiteral values."""
    text = html.unescape(value or "")
    text = _TAG_RE.sub(" ", text)
    return " ".join(text.split())


def _celex_id(raw: str) -> str | None:
    """Return bare CELEX id from ``celex:32016R0679`` style identifiers."""
    if not raw:
        return None
    if raw.startswith("celex:"):
        return raw.split(":", 1)[1]
    if raw.startswith("legissum:"):
        return None
    return raw


def _eurlex_uri(celex_raw: str, lang: str) -> str:
    celex = _celex_id(celex_raw)
    if celex:
        lang_code = lang.upper() if lang != "de" else "DE"
        if lang == "en":
            lang_code = "EN"
        elif lang == "fr":
            lang_code = "FR"
        elif lang == "it":
            lang_code = "IT"
        return f"https://eur-lex.europa.eu/legal-content/{lang_code}/TXT/?uri=CELEX:{celex}"
    ref = celex_raw.split(":", 1)[-1] if ":" in celex_raw else celex_raw
    return f"https://eur-lex.europa.eu/summary/{lang}/summary/{ref}"


def _sparql(query: str, *, timeout: int = 45) -> list[dict[str, str]]:
    body = urllib.parse.urlencode({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        SPARQL_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
            "User-Agent": "OpenGlossa/0.1 (+https://github.com/Joenvyme/openglossa)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"EUR-Lex SPARQL failed: {exc}") from exc
    bindings = (data.get("results") or {}).get("bindings") or []
    rows: list[dict[str, str]] = []
    for row in bindings:
        if not isinstance(row, dict):
            continue
        parsed: dict[str, str] = {}
        for key, val in row.items():
            if isinstance(val, dict):
                parsed[key] = str(val.get("value", ""))
        rows.append(parsed)
    return rows


def _sanitize_sparql(text: str) -> str:
    return text.replace("\\", " ").replace('"', " ").strip().casefold()


def _overlap_score(query: str, text: str) -> float:
    q = query.strip().casefold()
    if not q:
        return 0.0
    tn = text.casefold()
    if q in tn:
        return 1.0
    q_tokens = {t for t in q.split() if len(t) > 2}
    if not q_tokens:
        return 0.0
    doc_tokens = set(tn.split())
    return len(q_tokens & doc_tokens) / len(q_tokens)


def _build_search_query(
    query: str,
    src_lang: str,
    tgt_lang: str,
    *,
    limit: int,
) -> str:
    q = _sanitize_sparql(query)
    src_uri = _lang_uri(src_lang)
    tgt_uri = _lang_uri(tgt_lang)
    return f"""
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT ?celex ?src_text ?tgt_text WHERE {{
  {{
    ?work cdm:work_id_document ?celex .
    FILTER(STRSTARTS(STR(?celex), "celex:3"))
    ?se cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <{src_uri}> ;
       cdm:expression_title ?src_raw .
    FILTER(CONTAINS(LCASE(STR(?src_raw)), "{q}"))
    ?te cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <{tgt_uri}> ;
       cdm:expression_title ?tgt_raw .
    BIND(STR(?src_raw) AS ?src_text)
    BIND(STR(?tgt_raw) AS ?tgt_text)
  }}
  UNION {{
    ?work cdm:work_id_document ?celex .
    FILTER(STRSTARTS(STR(?celex), "legissum:"))
    ?se cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <{src_uri}> ;
       cdm:expression_abstract ?src_raw .
    FILTER(CONTAINS(LCASE(STR(?src_raw)), "{q}"))
    ?te cdm:expression_belongs_to_work ?work ;
       cdm:expression_uses_language <{tgt_uri}> ;
       cdm:expression_abstract ?tgt_raw .
    BIND(STR(?src_raw) AS ?src_text)
    BIND(STR(?tgt_raw) AS ?tgt_text)
  }}
}}
LIMIT {int(limit)}
"""


def search_parallel_live(
    text: str,
    src_lang: str,
    tgt_lang: str,
    k: int = 5,
    *,
    timeout: int = 45,
) -> list[dict[str, Any]]:
    """Live parallel segment search via CELLAR (titles + legissum summaries).

    Returns dicts shaped like ``search_parallel`` hits:
    ``{{src, tgt, source{{name, ref, uri, license}}, score}}``.
    """
    q = text.strip()
    if not q or src_lang not in SUPPORTED_LANGS or tgt_lang not in SUPPORTED_LANGS:
        return []
    if src_lang == tgt_lang:
        return []

    rows = _sparql(
        _build_search_query(q, src_lang, tgt_lang, limit=max(k * 3, 15)),
        timeout=timeout,
    )
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        celex = row.get("celex", "")
        src = _clean_literal(row.get("src_text", ""))
        tgt = _clean_literal(row.get("tgt_text", ""))
        if not src or not tgt:
            continue
        key = (src.casefold(), tgt.casefold())
        if key in seen:
            continue
        seen.add(key)
        score = _overlap_score(q, src)
        if score <= 0:
            continue
        ref = celex.split(":", 1)[-1] if ":" in celex else celex
        hits.append(
            {
                "src": src,
                "tgt": tgt,
                "source": {
                    "name": SOURCE_NAME,
                    "ref": ref,
                    "uri": _eurlex_uri(celex, src_lang),
                    "license": LICENSE_TAG,
                },
                "score": round(score, 4),
            }
        )
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:k]


def verify_live(
    src_term: str,
    tgt_term: str,
    src_lang: str,
    tgt_lang: str,
    *,
    limit: int = 5,
    timeout: int = 45,
) -> list[dict[str, Any]]:
    """Return EUR-Lex evidence when both terms co-occur in parallel EU texts."""
    s = src_term.strip()
    t = tgt_term.strip()
    if not s or not t:
        return []
    if src_lang not in SUPPORTED_LANGS or tgt_lang not in SUPPORTED_LANGS:
        return []

    rows = _sparql(
        _build_search_query(s, src_lang, tgt_lang, limit=max(limit * 4, 20)),
        timeout=timeout,
    )
    evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    st = t.casefold()
    for row in rows:
        celex = row.get("celex", "")
        tgt = _clean_literal(row.get("tgt_text", ""))
        if st not in tgt.casefold():
            continue
        ref = celex.split(":", 1)[-1] if ":" in celex else celex
        if ref in seen:
            continue
        seen.add(ref)
        evidence.append(
            {
                "name": SOURCE_NAME,
                "uri": _eurlex_uri(celex, src_lang),
                "license": LICENSE_TAG,
                "ref": ref,
            }
        )
        if len(evidence) >= limit:
            break
    return evidence
