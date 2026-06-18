from __future__ import annotations

import pytest

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


@pytest.fixture
def term_records() -> list[TermRecord]:
    return [
        TermRecord(
            concept_id="og:term:0001",
            domain=["obligations"],
            legal_basis=["SR 220 Art. 102"],
            definition={"fr": "Retard dans l'exécution d'une obligation."},
            terms={
                "de": [Term(text="Verzug", pos="noun", status=TermStatus.preferred)],
                "fr": [Term(text="demeure", pos="noun", status=TermStatus.preferred)],
                "it": [Term(text="mora", pos="noun", status=TermStatus.preferred)],
            },
            authority=Authority.statutory,
            sources=[
                SourceRef(
                    name="TERMDAT",
                    uri="https://www.termdat.bk.admin.ch/entry/1",
                    license="OGD-open-use",
                    ref="SR 220 Art. 102",
                )
            ],
        )
    ]


@pytest.fixture
def translation_units() -> list[TranslationUnit]:
    return [
        TranslationUnit(
            tu_id="og:tu:0001abcd",
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
    ]
