"""TERMDAT connector — official federal terminology database (~107K entries).

Status: 🟠 ORANGE. Free access via LINDAS, but **redistribution license is NOT
confirmed** (see LICENSING.md, hard rule #6). Therefore this connector is
**live-only**: it queries at request time (e.g. from the MCP server) and must
NOT bundle the raw upstream term text in downloadable dumps. Only derived data
(``concept_id`` + URI + identifier + available languages) may be persisted until
the license is confirmed (see :func:`derived_index`).

Data model (discovered live on LINDAS, graph ``lindas.admin.ch/fch/termdat``):
each entry is a ``schema:DefinedTerm`` resource
(``register.ld.admin.ch/termdat/{id}``) carrying multilingual ``schema:name``
(language-tagged), ``schema:description`` (definition), ``schema:citation``
(legal basis, with SR/RS references), ``schema:URL`` (citable), and an entry
status type (``ValidatedEntry`` / ``InProgressEntry``).

The ``sources`` extra (SPARQLWrapper) is required for live queries.
"""

from __future__ import annotations

import re

from openglossa.schemas import Authority, ReviewStatus, Term, TermRecord, TermStatus

ENDPOINT = "https://ld.admin.ch/query"
GRAPH = "https://lindas.admin.ch/fch/termdat"
SOURCE_NAME = "TERMDAT"
# Until confirmed, this tag signals "do not redistribute raw text".
LICENSE_TAG = "OGD-open-use-UNCONFIRMED"

CORE_LANGS = ("de", "fr", "it")
ALL_LANGS = ("de", "fr", "it", "rm", "en")

#: Hard rule #6 guard. Flip to True only once redistribution is confirmed in
#: LICENSING.md; exporters check this before persisting raw upstream text.
REDISTRIBUTION_CONFIRMED = False

# Field separators used inside GROUP_CONCAT (unlikely to occur in the data).
_KV = "\x1f"
_ITEM = "\x1e"

_VALIDATED = "https://schema.ld.admin.ch/ValidatedEntry"
_SR_RE = re.compile(r"\b(?:SR|RS)\s*\d+(?:\.\d+)*", re.IGNORECASE)


def assert_redistribution_allowed() -> None:
    """Raise unless TERMDAT redistribution has been confirmed (hard rule #6)."""
    if not REDISTRIBUTION_CONFIRMED:
        raise PermissionError(
            "TERMDAT redistribution is not confirmed (LICENSING.md). "
            "Live-only: do not bundle raw upstream text in dumps."
        )


def _sanitize(text: str) -> str:
    """Strip characters that could break the SPARQL string literal."""
    return text.replace("\\", " ").replace('"', " ").strip()


def build_lookup_query(query: str, src_lang: str, *, limit: int = 10) -> str:
    """SPARQL: entries whose ``src_lang`` name equals ``query`` (case-insensitive),
    with all language names, definitions, citations and status aggregated per entry.
    """
    q = _sanitize(query).lower()
    src = _sanitize(src_lang)
    return f"""
PREFIX schema: <http://schema.org/>
PREFIX la: <https://schema.ld.admin.ch/>
SELECT ?id ?url
  (GROUP_CONCAT(DISTINCT CONCAT(LANG(?name), "{_KV}", STR(?name)); separator="{_ITEM}") AS ?names)
  (GROUP_CONCAT(DISTINCT CONCAT(LANG(?def), "{_KV}", STR(?def)); separator="{_ITEM}") AS ?defs)
  (GROUP_CONCAT(DISTINCT STR(?cit); separator="{_ITEM}") AS ?cits)
  (GROUP_CONCAT(DISTINCT STR(?st); separator="{_ITEM}") AS ?statuses)
WHERE {{
  GRAPH <{GRAPH}> {{
    {{
      SELECT DISTINCT ?entry WHERE {{
        ?entry a schema:DefinedTerm ; schema:name ?src .
        FILTER(LANG(?src) = "{src}" && LCASE(STR(?src)) = "{q}")
      }} LIMIT {int(limit)}
    }}
    ?entry schema:identifier ?id .
    ?entry schema:name ?name .
    OPTIONAL {{ ?entry schema:URL ?url }}
    OPTIONAL {{ ?entry schema:description ?def }}
    OPTIONAL {{ ?entry schema:citation ?cit }}
    OPTIONAL {{ ?entry a ?st . FILTER(?st IN (la:ValidatedEntry, la:InProgressEntry)) }}
  }}
}}
GROUP BY ?id ?url
"""


def _parse_kv(value: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not value:
        return out
    for item in value.split(_ITEM):
        if _KV in item:
            lang, _, text = item.partition(_KV)
            text = text.strip()
            if text:
                out.append((lang, text))
    return out


def _parse_list(value: str) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(_ITEM) if v.strip()]


def _legal_basis(citations: list[str]) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for cit in citations:
        for m in _SR_RE.findall(cit):
            norm = re.sub(r"\s+", " ", m).upper().replace("RS", "SR")
            if norm not in seen:
                seen.add(norm)
                refs.append(norm)
    return refs


def _val(row: dict, key: str) -> str:
    return row.get(key, {}).get("value", "")


def row_to_term_record(row: dict, *, langs: tuple[str, ...] = ALL_LANGS) -> TermRecord | None:
    """Pure transform of an aggregated SPARQL row into a :class:`TermRecord`.

    Returns ``None`` if no term in the requested languages is present.
    """
    from openglossa.schemas import SourceRef

    entry_id = _val(row, "id")
    if not entry_id:
        return None

    names = _parse_kv(_val(row, "names"))
    terms: dict[str, list[Term]] = {}
    for lang, text in names:
        if lang not in langs:
            continue
        bucket = terms.setdefault(lang, [])
        status = TermStatus.preferred if not bucket else TermStatus.admitted
        bucket.append(Term(text=text, status=status))
    if not any(terms.values()):
        return None

    definition = {}
    for lang, text in _parse_kv(_val(row, "defs")):
        if lang in langs and lang not in definition:
            definition[lang] = text

    statuses = _parse_list(_val(row, "statuses"))
    review = ReviewStatus.verified if _VALIDATED in statuses else ReviewStatus.candidate

    url = _val(row, "url") or f"https://www.termdat.bk.admin.ch/entry/{entry_id}"

    return TermRecord(
        concept_id=f"og:term:termdat-{entry_id}",
        legal_basis=_legal_basis(_parse_list(_val(row, "cits"))),
        definition=definition,
        terms=terms,
        authority=Authority.administrative,
        sources=[
            SourceRef(
                name=SOURCE_NAME,
                uri=url,  # type: ignore[arg-type]
                license=LICENSE_TAG,
                ref=f"TERMDAT {entry_id}",
            )
        ],
        confidence=0.9 if review == ReviewStatus.verified else 0.5,
        review_status=review,
    )


def _run_sparql(query: str, *, timeout: int = 60) -> list[dict]:
    try:
        from SPARQLWrapper import JSON, SPARQLWrapper
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "TERMDAT live lookup requires the 'sources' extra: "
            "pip install 'openglossa[sources]'"
        ) from exc
    client = SPARQLWrapper(ENDPOINT)
    client.setQuery(query)
    client.setReturnFormat(JSON)
    client.setTimeout(timeout)
    client.addCustomHttpHeader("User-Agent", "OpenGlossa/0.1 (+https://github.com/openglossa)")
    client.addCustomHttpHeader("Accept", "application/sparql-results+json")
    return client.query().convert().get("results", {}).get("bindings", [])


def lookup_live(
    query: str,
    src_lang: str,
    *,
    langs: tuple[str, ...] = ALL_LANGS,
    limit: int = 10,
    timeout: int = 60,
) -> list[TermRecord]:
    """Live lookup against TERMDAT (LINDAS SPARQL).

    Returns concept records with multilingual equivalents, definitions and legal
    basis. Intended to be called at request time (e.g. by the MCP server), never
    to populate a redistributable dump (hard rule #6).
    """
    rows = _run_sparql(build_lookup_query(query, src_lang, limit=limit), timeout=timeout)
    records = [row_to_term_record(row, langs=langs) for row in rows]
    return [r for r in records if r is not None]


def derived_index(
    query: str,
    src_lang: str,
    *,
    limit: int = 10,
) -> list[dict]:
    """Redistribution-safe derived index for a lookup (NO raw term text).

    Honours hard rule #6: persists only ``concept_id`` + URI + identifier +
    available languages + legal basis — never the upstream term/definition text.
    """
    out: list[dict] = []
    for rec in lookup_live(query, src_lang, limit=limit):
        out.append(
            {
                "concept_id": rec.concept_id,
                "uri": str(rec.sources[0].uri),
                "identifier": rec.concept_id.removeprefix("og:term:termdat-"),
                "languages": rec.languages(),
                "legal_basis": rec.legal_basis,
            }
        )
    return out
