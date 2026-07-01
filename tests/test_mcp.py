from __future__ import annotations

from openglossa.mcp.server import (
    FEDLEX_NO_EN_NOTE,
    Repository,
    TERMDAT_EN_NOTE,
    get_official_text,
    lookup_term,
    search_parallel,
    suggest_glossary,
    verify_translation,
)
from openglossa.schemas import (
    Alignment,
    AlignmentMethod,
    Authority,
    SourceRef,
    Term,
    TermRecord,
    TermStatus,
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
    assert "en_scope" not in out


def test_lookup_term_de_en_includes_termdat_scope_note():
    repo = Repository()
    repo.terms = [
        TermRecord(
            concept_id="og:term:0002",
            terms={
                "de": [Term(text="Schuldner", status=TermStatus.preferred)],
                "en": [Term(text="debtor", status=TermStatus.preferred)],
            },
            authority=Authority.statutory,
            sources=[
                SourceRef(
                    name="TERMDAT",
                    uri="https://www.termdat.bk.admin.ch/entry/106263",
                    license="OGD-open-use",
                    ref="TERMDAT 106263",
                )
            ],
        )
    ]
    out = lookup_term(repo, "Schuldner", "de", "en")
    assert out["results"][0]["translations"] == ["debtor"]
    assert out["results"][0]["available_languages"] == ["de", "en"]
    assert out["en_scope"] == TERMDAT_EN_NOTE
    assert out["iate_scope"]  # informational whenever EN is involved


def test_lookup_term_de_en_with_iate_live(monkeypatch):
    repo = Repository()

    def fake_termdat(q, src, **kwargs):
        return []

    def fake_iate(q, src, **kwargs):
        from openglossa.schemas import Authority, ReviewStatus, SourceRef, Term, TermRecord, TermStatus

        return [
            TermRecord(
                concept_id="og:term:iate-99",
                terms={
                    "de": [Term(text="Schuldner", status=TermStatus.preferred)],
                    "en": [Term(text="obligor", status=TermStatus.preferred)],
                },
                authority=Authority.administrative,
                sources=[
                    SourceRef(
                        name="IATE",
                        uri="https://iate.europa.eu/entry/result/99",
                        license="EU-2011/833-reuse",
                        ref="IATE 99",
                    )
                ],
                review_status=ReviewStatus.verified,
            )
        ]

    import openglossa.sources.iate as iate_mod
    import openglossa.sources.termdat as termdat_mod

    monkeypatch.setattr(termdat_mod, "lookup_live", fake_termdat)
    monkeypatch.setattr(iate_mod, "lookup_live", fake_iate)
    out = lookup_term(repo, "Schuldner", "de", "en", termdat_live=True, iate_live=True)
    assert len(out["results"]) == 1
    assert out["results"][0]["translations"] == ["obligor"]
    assert out["results"][0]["sources"][0]["name"] == "IATE"
    assert out["en_scope"] == TERMDAT_EN_NOTE
    assert "iate_scope" in out


def test_verify_translation_en_via_termdat_live(monkeypatch):
    from openglossa.schemas import ReviewStatus

    repo = Repository()

    def fake_lookup(query, src_lang, **kwargs):
        assert query == "Schuldner"
        assert src_lang == "de"
        return [
            TermRecord(
                concept_id="og:term:termdat-106263",
                terms={
                    "de": [Term(text="Schuldner", status=TermStatus.preferred)],
                    "en": [Term(text="debtor", status=TermStatus.preferred)],
                },
                authority=Authority.administrative,
                sources=[
                    SourceRef(
                        name="TERMDAT",
                        uri="https://www.termdat.bk.admin.ch/entry/106263",
                        license="OGD-open-use-UNCONFIRMED",
                        ref="TERMDAT 106263",
                    )
                ],
                review_status=ReviewStatus.verified,
            )
        ]

    import openglossa.sources.termdat as termdat

    monkeypatch.setattr(termdat, "lookup_live", fake_lookup)
    out = verify_translation(repo, "Schuldner", "debtor", "de", "en", termdat_live=True)
    assert out["supported"] is True
    assert out["evidence"][0]["name"] == "TERMDAT"
    assert out["en_scope"] == TERMDAT_EN_NOTE


def test_get_official_text_rejects_english():
    out = get_official_text("SR 220 Art. 1", "en")
    assert out["text"] is None
    assert out["note"] == FEDLEX_NO_EN_NOTE


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
