from __future__ import annotations

from openglossa.sources.slds import rows_to_translation_units

# Mimics the real ipst/slds schema: one row per (decision_id, headnote_language).
_ROWS = [
    {
        "decision_id": "80 I 1",
        "decision_language": "de",
        "headnote": "Kantonales Zivilprozessrecht. Willkür.",
        "headnote_language": "de",
        "law_area": "constitutional law",
        "url": "https://www.bger.ch/atf/80-I-1",
    },
    {
        "decision_id": "80 I 1",
        "decision_language": "de",
        "headnote": "Procédure civile cantonale. Arbitraire.",
        "headnote_language": "fr",
        "law_area": "constitutional law",
        "url": "https://www.bger.ch/atf/80-I-1",
    },
    {
        "decision_id": "80 I 1",
        "decision_language": "de",
        "headnote": "Procedura civile cantonale. Arbitrio.",
        "headnote_language": "it",
        "law_area": "constitutional law",
        "url": "https://www.bger.ch/atf/80-I-1",
    },
]


def test_groups_by_decision_and_pairs_languages():
    tus = list(rows_to_translation_units(_ROWS))
    # 3 languages -> C(3,2) = 3 pairs for one decision.
    assert len(tus) == 3
    pairs = {(str(tu.src_lang), str(tu.tgt_lang)) for tu in tus}
    assert pairs == {("de", "fr"), ("de", "it"), ("fr", "it")}
    for tu in tus:
        assert tu.source.name == "SLDS"
        assert tu.source.license == "CC-BY-4.0"
        assert tu.source.ref == "ATF 80 I 1"
        assert tu.domain == ["constitutional law"]
        assert tu.alignment.method == "manual"
        assert str(tu.source.uri).startswith("https://www.bger.ch/")


def test_skips_incomplete_and_blank():
    rows = [
        {"decision_id": "1 A 1", "headnote": "Nur Deutsch.", "headnote_language": "de"},
        {"decision_id": "1 A 1", "headnote": "   ", "headnote_language": "fr"},  # blank
    ]
    # Only DE present (FR blank) -> no pair can be formed.
    assert list(rows_to_translation_units(rows)) == []


def test_dedup_keeps_first_per_language():
    rows = _ROWS + [
        {
            "decision_id": "80 I 1",
            "headnote": "DOUBLON à ignorer.",
            "headnote_language": "fr",
            "url": "https://www.bger.ch/atf/80-I-1",
        }
    ]
    tus = list(rows_to_translation_units(rows))
    de_fr = next(tu for tu in tus if (str(tu.src_lang), str(tu.tgt_lang)) == ("de", "fr"))
    assert de_fr.tgt == "Procédure civile cantonale. Arbitraire."
