"""Fedlex connector — Recueil systématique (RS) du droit fédéral suisse.

Fedlex publishes federal statutes in parallel DE/FR/IT, with rich RDF metadata
(JOLux ontology, ELI identifiers) and a SPARQL endpoint. License status: ✅ VERT
(reuse incl. commercial; cite the source; never present as the official text).

This module implements the first half of P1: given an RS number (e.g. "220" for
the Code of Obligations / Obligationenrecht), enumerate the ELI URIs of the three
language manifestations of the *consolidated* act, with provenance.

The heavy SPARQL dependency is optional (``pip install 'openglossa[sources]'``);
it is imported lazily so the rest of the package works without it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from openglossa.schemas import SourceRef

SPARQL_ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"
SOURCE_NAME = "Fedlex"
# Fedlex reuse condition; tracked in LICENSING.md as ✅ VERT.
LICENSE_TAG = "Fedlex-open-reuse"

CORE_LANGS = ("de", "fr", "it")

# Map ISO 639-1 -> Fedlex/JOLux language URIs.
_LANG_URI = {
    "de": "http://publications.europa.eu/resource/authority/language/DEU",
    "fr": "http://publications.europa.eu/resource/authority/language/FRA",
    "it": "http://publications.europa.eu/resource/authority/language/ITA",
    "rm": "http://publications.europa.eu/resource/authority/language/ROH",
    "en": "http://publications.europa.eu/resource/authority/language/ENG",
}


@dataclass
class ActManifestation:
    """One language manifestation of a consolidated act."""

    rs_number: str
    lang: str
    eli_uri: str
    title: str | None = None
    file_url: str | None = None  # HTML/XML manifestation in the filestore
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_source_ref(self) -> SourceRef:
        return SourceRef(
            name=SOURCE_NAME,
            uri=self.eli_uri,  # type: ignore[arg-type]
            license=LICENSE_TAG,
            ref=f"SR {self.rs_number}",
            retrieved_at=self.retrieved_at,
        )


def _build_query(rs_number: str) -> str:
    """SPARQL: latest in-force consolidation of an act + its language expressions.

    Returns one row per (language, expression, manifestation file).
    """
    return f"""
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#>

SELECT ?consolidation ?language ?title ?fileUrl WHERE {{
  ?act a jolux:Act ;
       jolux:classifiedByTaxonomyEntry/skos:notation ?rs .
  FILTER(STR(?rs) = "{rs_number}")

  ?act jolux:isRealizedBy ?expression .
  ?expression jolux:language ?language ;
              jolux:title ?title .

  OPTIONAL {{
    ?expression jolux:isEmbodiedBy ?manifestation .
    ?manifestation jolux:isExemplifiedBy ?fileUrl .
  }}

  ?act jolux:dateApplicability ?from .
  FILTER(?from <= NOW())
  OPTIONAL {{ ?act jolux:dateNoLongerInForce ?until . }}
  FILTER(!BOUND(?until) || ?until > NOW())
}}
ORDER BY ?language
"""


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
        Languages to keep (default DE/FR/IT).

    Returns one :class:`ActManifestation` per requested language found.

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

    wanted_uris = {_LANG_URI[lang]: lang for lang in langs if lang in _LANG_URI}

    client = SPARQLWrapper(endpoint)
    client.setQuery(_build_query(rs_number))
    client.setReturnFormat(JSON)
    client.setTimeout(timeout)
    client.addCustomHttpHeader("User-Agent", "OpenGlossa/0.1 (+https://github.com/openglossa)")

    results = client.query().convert()
    bindings = results.get("results", {}).get("bindings", [])

    seen: dict[str, ActManifestation] = {}
    for row in bindings:
        lang_uri = row.get("language", {}).get("value")
        lang = wanted_uris.get(lang_uri)
        if lang is None or lang in seen:
            continue
        seen[lang] = ActManifestation(
            rs_number=rs_number,
            lang=lang,
            eli_uri=row.get("consolidation", {}).get("value")
            or row.get("fileUrl", {}).get("value", ""),
            title=row.get("title", {}).get("value"),
            file_url=row.get("fileUrl", {}).get("value"),
        )

    return [seen[lang] for lang in langs if lang in seen]


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    # Smoke test on SR 220 (Code of Obligations / Obligationenrecht / Codice obbligazioni).
    for m in fetch_act_manifestations("220"):
        print(f"[{m.lang}] {m.title}\n  {m.eli_uri}")
