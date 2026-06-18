from __future__ import annotations

from openglossa.mcp.server import (
    Repository,
    lookup_term,
    search_parallel,
    verify_translation,
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
