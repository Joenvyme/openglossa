from __future__ import annotations

from openglossa.mcp.server import (
    Repository,
    get_official_text,
    lookup_term,
    search_parallel,
    suggest_glossary,
    verify_translation,
)
from openglossa.schemas import (
    Alignment,
    AlignmentMethod,
    SourceRef,
    TranslationUnit,
)


def _repo(term_records, translation_units) -> Repository:
    repo = Repository()
    repo.terms = term_records
    repo.tus = translation_units
    return repo


def test_lookup_term_returns_citations(term_records, translation_units):
    repo = _repo(term_records, translation_units)
    out = lookup_term(repo, "Verzug", "de", "fr")
    assert out["results"]
    res = out["results"][0]
    assert "demeure" in res["translations"]
    assert res["sources"][0]["name"] == "TERMDAT"
    assert "disclaimer" in out


def test_verify_translation_supported(term_records, translation_units):
    repo = _repo(term_records, translation_units)
    out = verify_translation(repo, "Verzug", "demeure", "de", "fr")
    assert out["supported"] is True
    assert out["evidence"]


def test_verify_translation_unsupported_does_not_fabricate(term_records, translation_units):
    repo = _repo(term_records, translation_units)
    out = verify_translation(repo, "Verzug", "inexistant", "de", "fr")
    assert out["supported"] is False
    assert out["evidence"] == []


def test_search_parallel(term_records, translation_units):
    repo = _repo(term_records, translation_units)
    out = search_parallel(repo, "Schuldner Verzug", "de", "fr", k=3)
    assert out["results"]
    assert out["results"][0]["source"]["name"] == "SLDS"


def test_search_parallel_handles_reversed_orientation(term_records):
    reversed_tu = TranslationUnit(
        tu_id="og:tu:rev00001",
        src_lang="fr",
        tgt_lang="de",
        src="Le débiteur est en demeure.",
        tgt="Der Schuldner kommt in Verzug.",
        source=SourceRef(
            name="Fedlex",
            uri="https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de",
            license="Fedlex-open-reuse",
            ref="SR 220 Art. 102",
        ),
        alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
    )
    repo = _repo(term_records, [reversed_tu])
    out = search_parallel(repo, "Schuldner Verzug", "de", "fr", k=3)
    assert out["results"]
    assert out["results"][0]["src"] == "Der Schuldner kommt in Verzug."


def test_verify_translation_via_official_tm(term_records, translation_units):
    repo = _repo([], translation_units)  # no termbase, only the official TM
    out = verify_translation(repo, "Schuldner", "demeure", "de", "fr")
    assert out["supported"] is True
    assert out["evidence"][0]["name"] == "SLDS"


def test_suggest_glossary_extracts_terms_with_citations(term_records, translation_units):
    repo = _repo(term_records, translation_units)
    out = suggest_glossary(repo, "Der Schuldner kommt in Verzug heute.", "de", "fr")
    assert out["results"]
    hit = out["results"][0]
    assert hit["term"] == "Verzug"
    assert hit["translation"] == "demeure"
    assert hit["sources"][0]["name"] == "TERMDAT"
    assert "disclaimer" in out


def test_get_official_text_delegates_to_fedlex(monkeypatch):
    import openglossa.sources.fedlex as fedlex

    def fake(eli_or_citation: str, lang: str, **_):
        return {
            "text": "Der Vertrag ist vollkommen.",
            "uri": "https://fedlex.data.admin.ch/eli/cc/27/.../de#art_1",
            "lang": lang,
            "ref": "SR 220 Art. 1",
        }

    monkeypatch.setattr(fedlex, "fetch_official_text", fake)
    out = get_official_text("SR 220 Art. 1", "de")
    assert out["text"] == "Der Vertrag ist vollkommen."
    assert out["ref"] == "SR 220 Art. 1"
    assert "disclaimer" in out


def test_get_official_text_handles_errors(monkeypatch):
    import openglossa.sources.fedlex as fedlex

    def boom(*_, **__):
        raise RuntimeError("network down")

    monkeypatch.setattr(fedlex, "fetch_official_text", boom)
    out = get_official_text("SR 220 Art. 1", "de")
    assert out["text"] is None
    assert "network down" in out["error"]
    assert "disclaimer" in out
