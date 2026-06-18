from __future__ import annotations

import pytest

from openglossa.sources import termdat
from openglossa.sources.termdat import _ITEM, _KV, build_lookup_query, row_to_term_record


def _row(names, defs="", cits="", statuses=termdat._VALIDATED, entry_id="109123"):
    return {
        "id": {"value": entry_id},
        "url": {"value": f"https://www.termdat.bk.admin.ch/entry/{entry_id}"},
        "names": {"value": names},
        "defs": {"value": defs},
        "cits": {"value": cits},
        "statuses": {"value": statuses},
    }


def _kv_items(pairs):
    return _ITEM.join(f"{lang}{_KV}{text}" for lang, text in pairs)


def test_row_to_term_record_multilingual():
    row = _row(
        names=_kv_items([("de", "Motion"), ("fr", "motion"), ("it", "mozione"), ("en", "motion")]),
        defs=_kv_items([("de", "Parlamentarischer Vorstoss"), ("fr", "Intervention parlementaire")]),
        cits=_ITEM.join([
            "Parlamentsgesetz, Tit. vor Art. 120 (SR 171.10, Stand 2016-03)",
            "LF Parlement (RS 171.10)",
        ]),
    )
    rec = row_to_term_record(row)
    assert rec is not None
    assert rec.concept_id == "og:term:termdat-109123"
    assert rec.preferred("de") == "Motion"
    assert rec.preferred("it") == "mozione"
    assert set(rec.languages()) == {"de", "fr", "it", "en"}
    assert rec.definition["fr"] == "Intervention parlementaire"
    assert rec.legal_basis == ["SR 171.10"]  # deduped, normalized
    assert rec.review_status == "verified"
    assert rec.sources[0].name == "TERMDAT"
    assert rec.sources[0].license == "OGD-open-use-UNCONFIRMED"


def test_row_to_term_record_lang_filter_and_status():
    row = _row(
        names=_kv_items([("de", "Begriff"), ("ro", "ignored")]),
        statuses="https://schema.ld.admin.ch/InProgressEntry",
    )
    rec = row_to_term_record(row, langs=("de", "fr", "it"))
    assert rec is not None
    assert set(rec.languages()) == {"de"}
    assert rec.review_status == "candidate"
    assert rec.confidence == 0.5


def test_row_to_term_record_none_when_no_terms():
    assert row_to_term_record(_row(names="")) is None


def test_build_lookup_query_sanitizes():
    q = build_lookup_query('Mo"tion\\x', "de", limit=5)
    assert "mo tion x" in q  # quotes/backslash removed, lowercased
    assert "LIMIT 5" in q
    assert "fch/termdat" in q


def test_redistribution_guard():
    assert termdat.REDISTRIBUTION_CONFIRMED is False
    with pytest.raises(PermissionError):
        termdat.assert_redistribution_allowed()
