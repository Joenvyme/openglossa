from __future__ import annotations

from openglossa.sources import iate
from openglossa.sources.iate import entry_to_term_record


def _sample_item():
    return {
        "id": 3585531,
        "code": "D4657CF0A8BB4A0EB5DE993BB5E7DABF",
        "language": {
            "de": {
                "term_entries": [
                    {
                        "term_value": "Verjährung",
                        "metadata": {"reliability": {"code": 4, "name": "most reliable"}},
                    }
                ]
            },
            "en": {
                "term_entries": [
                    {
                        "term_value": "limitation",
                        "metadata": {"reliability": {"code": 4, "name": "most reliable"}},
                    },
                    {
                        "term_value": "negative prescription",
                        "metadata": {"reliability": {"code": 3, "name": "reliable"}},
                    },
                ]
            },
            "fr": {
                "term_entries": [
                    {
                        "term_value": "prescription extinctive",
                        "metadata": {"reliability": {"code": 4, "name": "most reliable"}},
                    }
                ]
            },
        },
    }


def test_entry_to_term_record_multilingual():
    rec = entry_to_term_record(_sample_item())
    assert rec is not None
    assert rec.concept_id == "og:term:iate-3585531"
    assert rec.preferred("de") == "Verjährung"
    assert rec.preferred("en") == "limitation"
    assert rec.preferred("fr") == "prescription extinctive"
    assert rec.sources[0].name == "IATE"
    assert rec.sources[0].license == "EU-2011/833-reuse"
    assert "3585531" in str(rec.sources[0].uri)


def test_lookup_live_parses_api(monkeypatch):
    def fake_post(payload, *, timeout=30):
        assert payload["query"] == "Verjährung"
        assert payload["source"] == "de"
        return [_sample_item()]

    monkeypatch.setattr(iate, "_post_search", fake_post)
    records = iate.lookup_live("Verjährung", "de", langs=("de", "en", "fr"))
    assert len(records) == 1
    assert records[0].preferred("en") == "limitation"


def test_reliability_code_accepts_int_or_dict():
    from openglossa.sources.iate import _reliability_code

    assert _reliability_code({"metadata": {"reliability": 3}}) == 3
    assert _reliability_code({"metadata": {"reliability": {"code": 4}}}) == 4
    assert _reliability_code({}) == 0


def test_redistribution_allowed():
    assert iate.REDISTRIBUTION_CONFIRMED is True
    iate.assert_redistribution_allowed()
