from __future__ import annotations

import pytest
from pydantic import ValidationError

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


def _source() -> SourceRef:
    return SourceRef(
        name="TERMDAT",
        uri="https://www.termdat.bk.admin.ch/entry/123",
        license="OGD-open-use",
        ref="SR 220 Art. 102",
    )


def test_term_record_valid_and_preferred():
    rec = TermRecord(
        concept_id="og:term:0001",
        domain=["civil_law", "obligations"],
        legal_basis=["SR 220 Art. 102"],
        definition={"de": "...", "fr": "...", "it": "..."},
        terms={
            "de": [Term(text="Verzug", pos="noun", status=TermStatus.preferred)],
            "fr": [Term(text="demeure", pos="noun", status=TermStatus.preferred)],
            "it": [Term(text="mora", pos="noun", status=TermStatus.preferred)],
        },
        authority=Authority.statutory,
        sources=[_source()],
        confidence=0.92,
    )
    assert rec.preferred("fr") == "demeure"
    assert set(rec.languages()) == {"de", "fr", "it"}


def test_term_record_requires_a_term():
    with pytest.raises(ValidationError):
        TermRecord(
            concept_id="og:term:empty",
            authority=Authority.statutory,
            sources=[_source()],
            terms={},
        )


def test_term_record_requires_provenance():
    with pytest.raises(ValidationError):
        TermRecord(
            concept_id="og:term:noprov",
            authority=Authority.statutory,
            sources=[],
            terms={"de": [Term(text="Verzug")]},
        )


def test_concept_id_pattern():
    with pytest.raises(ValidationError):
        TermRecord(
            concept_id="bad-id",
            authority=Authority.statutory,
            sources=[_source()],
            terms={"de": [Term(text="Verzug")]},
        )


def test_translation_unit_valid():
    tu = TranslationUnit(
        tu_id="og:tu:7f3a0011",
        src_lang="de",
        tgt_lang="fr",
        src="Der Schuldner kommt in Verzug.",
        tgt="Le débiteur est en demeure.",
        domain=["obligations"],
        source=SourceRef(
            name="SLDS",
            uri="https://huggingface.co/datasets/ipst/slds",
            license="CC-BY-4.0",
            ref="BGE 146 IV 226",
        ),
        alignment=Alignment(method=AlignmentMethod.eli_structural, score=0.98),
    )
    assert tu.src_lang == "de"


def test_translation_unit_rejects_same_langs():
    with pytest.raises(ValidationError):
        TranslationUnit(
            tu_id="og:tu:same",
            src_lang="de",
            tgt_lang="de",
            src="x",
            tgt="y",
            source=SourceRef(name="SLDS", uri="https://example.org", license="CC-BY-4.0"),
            alignment=Alignment(method=AlignmentMethod.manual),
        )


def test_json_schema_export(tmp_path):
    from openglossa.schemas import export_json_schemas

    paths = export_json_schemas(tmp_path)
    assert {p.name for p in paths} == {
        "term_record.schema.json",
        "translation_unit.schema.json",
        "term_candidate.schema.json",
    }
    for p in paths:
        assert p.read_text(encoding="utf-8").strip().startswith("{")
