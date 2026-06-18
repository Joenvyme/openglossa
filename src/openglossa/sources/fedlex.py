"""Fedlex connector — Recueil systématique (RS) du droit fédéral suisse.

Fedlex publishes federal statutes in parallel DE/FR/IT (+ EN/RM where available),
with RDF metadata (JOLux ontology, ELI identifiers) behind a SPARQL endpoint.
License status: ✅ VERT (reuse incl. commercial; cite the source; never present as
the official text).

This implements task §10.2 / P1 (first half): given an RS number (e.g. ``"220"``
for the Code of Obligations / Obligationenrecht / Codice delle obbligazioni),
resolve the **consolidated** act (ELI ``/eli/cc/...``) and return one
:class:`ActManifestation` per language, with provenance. It also builds
title-level parallel :class:`TranslationUnit` records — the act titles are
official, structurally-aligned parallel text and make a clean, citable TM seed.

The SPARQL query was validated live against the Fedlex endpoint. The heavy
dependency (SPARQLWrapper) is optional (``pip install 'openglossa[sources]'``).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import combinations

from openglossa.schemas import (
    Alignment,
    AlignmentMethod,
    Lang,
    SourceRef,
    TranslationUnit,
)

SPARQL_ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"
SOURCE_NAME = "Fedlex"
# Fedlex reuse condition; tracked in LICENSING.md as ✅ VERT.
LICENSE_TAG = "Fedlex-open-reuse"

CORE_LANGS = ("de", "fr", "it")

# Map EU Vocabularies language authority URIs -> ISO 639-1.
_LANG_BY_URI = {
    "http://publications.europa.eu/resource/authority/language/DEU": "de",
    "http://publications.europa.eu/resource/authority/language/FRA": "fr",
    "http://publications.europa.eu/resource/authority/language/ITA": "it",
    "http://publications.europa.eu/resource/authority/language/ROH": "rm",
    "http://publications.europa.eu/resource/authority/language/ENG": "en",
}


@dataclass
class ActManifestation:
    """One language expression of a consolidated act."""

    rs_number: str
    lang: str
    eli_uri: str
    title: str | None = None
    file_url: str | None = None  # HTML manifestation in the filestore, if present
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_source_ref(self) -> SourceRef:
        return SourceRef(
            name=SOURCE_NAME,
            uri=self.eli_uri,  # type: ignore[arg-type]
            license=LICENSE_TAG,
            ref=f"SR {self.rs_number}",
            retrieved_at=self.retrieved_at,
        )


def build_query(rs_number: str) -> str:
    """SPARQL: the in-force consolidated (cc) act for an RS number + its language
    expressions (title and, when available, the HTML manifestation).
    """
    return f"""
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#>
SELECT ?act ?lang ?title ?fileUrl WHERE {{
  ?entry skos:notation ?notation .
  FILTER(STR(?notation) = "{rs_number}")
  FILTER(CONTAINS(STR(?entry), "/legal-taxonomy/"))

  ?act jolux:classifiedByTaxonomyEntry ?entry .
  FILTER(CONTAINS(STR(?act), "/eli/cc/"))
  OPTIONAL {{ ?act jolux:dateNoLongerInForce ?dnlif . }}
  FILTER(!BOUND(?dnlif) || ?dnlif > NOW())

  ?act jolux:isRealizedBy ?expr .
  ?expr jolux:language ?lang ;
        jolux:title ?title .
  OPTIONAL {{
    ?expr jolux:isEmbodiedBy ?manif .
    ?manif jolux:isExemplifiedBy ?fileUrl ;
           jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/html> .
  }}
}}
"""


def bindings_to_manifestations(
    rs_number: str,
    bindings: Iterable[dict],
    *,
    langs: tuple[str, ...] = CORE_LANGS,
) -> list[ActManifestation]:
    """Pure transform of SPARQL JSON bindings into manifestations (one per lang).

    Kept separate from the network call so it can be unit-tested offline.
    """
    wanted = set(langs)
    seen: dict[str, ActManifestation] = {}
    for row in bindings:
        lang_uri = row.get("lang", {}).get("value", "")
        lang = _LANG_BY_URI.get(lang_uri)
        if lang is None or lang not in wanted:
            continue
        existing = seen.get(lang)
        file_url = row.get("fileUrl", {}).get("value") or None
        if existing is None:
            seen[lang] = ActManifestation(
                rs_number=rs_number,
                lang=lang,
                eli_uri=row.get("act", {}).get("value", ""),
                title=row.get("title", {}).get("value"),
                file_url=file_url,
            )
        elif existing.file_url is None and file_url:
            existing.file_url = file_url
    return [seen[lang] for lang in langs if lang in seen]


def fetch_act_manifestations(
    rs_number: str,
    *,
    langs: tuple[str, ...] = CORE_LANGS,
    endpoint: str = SPARQL_ENDPOINT,
    timeout: int = 60,
) -> list[ActManifestation]:
    """Query Fedlex SPARQL for the in-force consolidation of an act.

    Parameters
    ----------
    rs_number:
        The systematic-collection number, e.g. ``"220"`` (Code of Obligations).
    langs:
        Languages to keep (default DE/FR/IT; ``"en"``/``"rm"`` also supported).

    Raises
    ------
    ImportError
        If the optional ``sources`` extra (SPARQLWrapper) is not installed.
    """
    try:
        from SPARQLWrapper import JSON, SPARQLWrapper
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "fetch_act_manifestations requires the 'sources' extra: "
            "pip install 'openglossa[sources]'"
        ) from exc

    client = SPARQLWrapper(endpoint)
    client.setQuery(build_query(rs_number))
    client.setReturnFormat(JSON)
    client.setTimeout(timeout)
    client.addCustomHttpHeader("User-Agent", "OpenGlossa/0.1 (+https://github.com/openglossa)")

    results = client.query().convert()
    bindings = results.get("results", {}).get("bindings", [])
    return bindings_to_manifestations(rs_number, bindings, langs=langs)


def _tu_id(rs: str, src_lang: str, tgt_lang: str, src: str, tgt: str) -> str:
    digest = hashlib.sha1(f"{rs}|{src_lang}|{tgt_lang}|{src}|{tgt}".encode()).hexdigest()[:16]
    return f"og:tu:{digest}"


def manifestations_to_title_units(
    manifestations: Iterable[ActManifestation],
    *,
    langs: tuple[str, ...] = CORE_LANGS,
) -> list[TranslationUnit]:
    """Build title-level parallel TUs from an act's language manifestations.

    Act titles are official, structurally-aligned parallel text — a clean,
    citable TM seed (alignment method ``eli-structural``).
    """
    by_lang = {m.lang: m for m in manifestations}
    units: list[TranslationUnit] = []
    for src_lang, tgt_lang in combinations(langs, 2):
        src_m = by_lang.get(src_lang)
        tgt_m = by_lang.get(tgt_lang)
        if not src_m or not tgt_m or not src_m.title or not tgt_m.title:
            continue
        units.append(
            TranslationUnit(
                tu_id=_tu_id(src_m.rs_number, src_lang, tgt_lang, src_m.title, tgt_m.title),
                src_lang=Lang(src_lang),
                tgt_lang=Lang(tgt_lang),
                src=src_m.title,
                tgt=tgt_m.title,
                domain=["statute-title"],
                source=src_m.to_source_ref(),
                alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
            )
        )
    return units


def fetch_title_translation_units(
    rs_number: str,
    *,
    langs: tuple[str, ...] = CORE_LANGS,
) -> list[TranslationUnit]:
    """Convenience: fetch an act and return its title-level parallel TUs."""
    manifs = fetch_act_manifestations(rs_number, langs=langs)
    return manifestations_to_title_units(manifs, langs=langs)


# --------------------------------------------------------------------------- #
# Article-level ingestion (P1 full): in-force consolidation -> Akoma Ntoso -> TUs
# --------------------------------------------------------------------------- #

_USER_FORMAT = "https://fedlex.data.admin.ch/vocabulary/user-format"


def _run_sparql(query: str, *, endpoint: str = SPARQL_ENDPOINT, timeout: int = 90) -> list[dict]:
    try:
        from SPARQLWrapper import JSON, SPARQLWrapper
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "This feature requires the 'sources' extra: pip install 'openglossa[sources]'"
        ) from exc
    client = SPARQLWrapper(endpoint)
    client.setQuery(query)
    client.setReturnFormat(JSON)
    client.setTimeout(timeout)
    client.addCustomHttpHeader("User-Agent", "OpenGlossa/0.1 (+https://github.com/openglossa)")
    return client.query().convert().get("results", {}).get("bindings", [])


def resolve_cc_uri(rs_number: str, *, endpoint: str = SPARQL_ENDPOINT) -> str | None:
    """Return the consolidated-act (``/eli/cc/...``) URI for an RS number."""
    bindings = _run_sparql(build_query(rs_number), endpoint=endpoint)
    for row in bindings:
        act = row.get("act", {}).get("value", "")
        if "/eli/cc/" in act:
            return act
    return None


@dataclass
class ConsolidationSource:
    """A downloadable manifestation of the in-force consolidation, per language."""

    lang: str
    citable_uri: str  # ELI expression URI (citable)
    file_url: str  # filestore URL of the chosen format (xml/html)


def _consolidation_query(cc_uri: str, fmt: str) -> str:
    return f"""
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?lang ?expr ?url WHERE {{
  {{
    SELECT (MAX(?d) AS ?maxdate) WHERE {{
      ?cons jolux:isMemberOf <{cc_uri}> ; jolux:dateApplicability ?d .
      FILTER(?d <= NOW())
    }}
  }}
  ?cons jolux:isMemberOf <{cc_uri}> ;
        jolux:dateApplicability ?maxdate ;
        jolux:isRealizedBy ?expr .
  ?expr jolux:language ?lang ;
        jolux:isEmbodiedBy ?m .
  ?m jolux:isExemplifiedBy ?url ;
     jolux:userFormat <{_USER_FORMAT}/{fmt}> .
}}
"""


def fetch_consolidation_sources(
    rs_number: str,
    *,
    langs: tuple[str, ...] = CORE_LANGS,
    fmt: str = "xml",
    endpoint: str = SPARQL_ENDPOINT,
) -> list[ConsolidationSource]:
    """Resolve the in-force consolidation's downloadable manifestation per language."""
    cc_uri = resolve_cc_uri(rs_number, endpoint=endpoint)
    if cc_uri is None:
        return []
    wanted = set(langs)
    out: dict[str, ConsolidationSource] = {}
    for row in _run_sparql(_consolidation_query(cc_uri, fmt), endpoint=endpoint):
        lang = _LANG_BY_URI.get(row.get("lang", {}).get("value", ""))
        if lang is None or lang not in wanted or lang in out:
            continue
        out[lang] = ConsolidationSource(
            lang=lang,
            citable_uri=row.get("expr", {}).get("value", ""),
            file_url=row.get("url", {}).get("value", ""),
        )
    return [out[lang] for lang in langs if lang in out]


def _download(url: str, *, timeout: int = 90) -> str:
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Downloading requires the 'sources' extra: pip install 'openglossa[sources]'"
        ) from exc
    resp = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "OpenGlossa/0.1 (+https://github.com/openglossa)"},
    )
    resp.raise_for_status()
    return resp.text


def fetch_article_translation_units(
    rs_number: str,
    *,
    langs: tuple[str, ...] = CORE_LANGS,
    limit: int = 0,
    endpoint: str = SPARQL_ENDPOINT,
) -> list[TranslationUnit]:
    """Full P1: in-force consolidation -> Akoma Ntoso XML -> eId-aligned TUs.

    Downloads the XML manifestation of each requested language, parses it into
    ``eId -> text`` segments, and aligns by shared ``eId`` (article/alinéa).

    Parameters
    ----------
    limit:
        Max number of aligned eIds (0 = all). Use a small value for a verifiable
        slice.
    """
    from openglossa.align.eli_structural import align_segments
    from openglossa.sources.akn import parse_segments

    sources = fetch_consolidation_sources(rs_number, langs=langs, fmt="xml", endpoint=endpoint)
    if len(sources) < 2:
        return []

    segments_by_lang: dict[str, dict[str, str]] = {}
    citable_uri_by_lang: dict[str, str] = {}
    for src in sources:
        segments_by_lang[src.lang] = parse_segments(_download(src.file_url))
        citable_uri_by_lang[src.lang] = src.citable_uri

    present = tuple(lang for lang in langs if segments_by_lang.get(lang))
    return align_segments(
        rs_number,
        segments_by_lang,
        langs=present,
        citable_uri_by_lang=citable_uri_by_lang,
        limit=limit,
    )


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    for m in fetch_act_manifestations("220", langs=("de", "fr", "it", "rm", "en")):
        print(f"[{m.lang}] {m.title}\n  {m.eli_uri}")
