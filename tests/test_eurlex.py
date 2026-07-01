from __future__ import annotations

from openglossa.sources import eurlex
from openglossa.sources.eurlex import _clean_literal, _overlap_score


def test_clean_literal_strips_xml():
    raw = "<div>EU <b>data</b> protection &amp; privacy</div>"
    assert _clean_literal(raw) == "EU data protection & privacy"


def test_overlap_score_phrase_and_tokens():
    assert _overlap_score("Schuldner", "Mehrwertsteuerschuldner") == 1.0
    assert _overlap_score("foo bar", "foo baz") == 0.5


def test_search_parallel_live_parses_sparql(monkeypatch):
    def fake_sparql(query, *, timeout=45):
        assert "Schuldner" in query or "schuldner" in query
        return [
            {
                "celex": "celex:32000L0065",
                "src_text": (
                    "Richtlinie 2000/65/EG — Bestimmung des Mehrwertsteuerschuldners"
                ),
                "tgt_text": (
                    "Council Directive 2000/65/EC — person liable for payment of VAT"
                ),
            }
        ]

    monkeypatch.setattr(eurlex, "_sparql", fake_sparql)
    hits = eurlex.search_parallel_live("Schuldner", "de", "en", k=3)
    assert len(hits) == 1
    assert "Schuldner" in hits[0]["src"]
    assert hits[0]["source"]["name"] == "EUR-Lex"
    assert hits[0]["source"]["license"] == "CC-BY-4.0-EU"
    assert "32000L0065" in hits[0]["source"]["ref"]


def test_verify_live_requires_tgt_term(monkeypatch):
    def fake_sparql(query, *, timeout=45):
        return [
            {
                "celex": "celex:32000L0065",
                "src_text": "Mehrwertsteuerschuldner",
                "tgt_text": "person liable for payment of value added tax",
            }
        ]

    monkeypatch.setattr(eurlex, "_sparql", fake_sparql)
    ev = eurlex.verify_live("Schuldner", "liable", "de", "en")
    assert len(ev) == 1
    assert ev[0]["name"] == "EUR-Lex"


def test_redistribution_allowed():
    assert eurlex.REDISTRIBUTION_CONFIRMED is True
    eurlex.assert_redistribution_allowed()
