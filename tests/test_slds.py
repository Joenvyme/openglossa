from __future__ import annotations

from openglossa.sources.slds import rows_to_translation_units


def test_rows_to_translation_units_builds_pairs():
    rows = [
        {
            "regeste_de": "Der Schuldner kommt in Verzug.",
            "regeste_fr": "Le débiteur est en demeure.",
            "regeste_it": "Il debitore è in mora.",
            "bge": "BGE 146 IV 226",
        }
    ]
    tus = list(rows_to_translation_units(rows))
    # 3 languages -> C(3,2) = 3 pairs.
    assert len(tus) == 3
    pairs = {(str(tu.src_lang), str(tu.tgt_lang)) for tu in tus}
    assert pairs == {("de", "fr"), ("de", "it"), ("fr", "it")}
    for tu in tus:
        assert tu.source.name == "SLDS"
        assert tu.source.license == "CC-BY-4.0"
        assert tu.source.ref == "BGE 146 IV 226"


def test_rows_dedup_and_skip_incomplete():
    rows = [
        {"regeste_de": "A", "regeste_fr": "B"},
        {"regeste_de": "A", "regeste_fr": "B"},  # duplicate
        {"regeste_de": "only german"},  # incomplete -> skipped
    ]
    tus = list(rows_to_translation_units(rows))
    assert len(tus) == 1
