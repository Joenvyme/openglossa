from __future__ import annotations

from openglossa.mining import candidate_terms, extract_candidates, mine_pairs, verify
from openglossa.schemas import (
    Alignment,
    AlignmentMethod,
    SourceRef,
    TermCandidate,
    TranslationUnit,
)

# A tiny parallel corpus where "Schuldner"/"débiteur" and "Verzug"/"demeure"
# co-occur consistently across distinct articles, plus noise that should not pair.
_PAIRS = [
    ("Der Schuldner kommt in Verzug.", "Le débiteur est en demeure."),
    ("Der Schuldner haftet bei Verzug.", "Le débiteur répond en cas de demeure."),
    ("Bei Verzug schuldet der Schuldner Zins.", "En cas de demeure le débiteur doit un intérêt."),
    # "Schuldner"/"débiteur" also appear WITHOUT Verzug/demeure, so co-occurrence
    # can separate the two pairs instead of treating them as collinear.
    ("Der Schuldner zahlt die Schuld.", "Le débiteur paie la dette."),
    ("Der Schuldner erfüllt die Pflicht.", "Le débiteur exécute l'obligation."),
    ("Die Katze schläft im Garten.", "Le chat dort dans le jardin."),
]


def _tus() -> list[TranslationUnit]:
    tus: list[TranslationUnit] = []
    for i, (de, fr) in enumerate(_PAIRS):
        tus.append(
            TranslationUnit(
                tu_id=f"og:tu:mine{i:04d}",
                src_lang="de",
                tgt_lang="fr",
                src=de,
                tgt=fr,
                source=SourceRef(
                    name="Fedlex",
                    uri=f"https://www.fedlex.admin.ch/eli/cc/24/233_245_233/de#art_{i}",
                    license="OGD-open-use",
                    ref=f"SR 220 Art. {i + 1}",
                ),
                alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
            )
        )
    return tus


def test_candidate_terms_filters_stopwords_and_rare() -> None:
    df = candidate_terms([de for de, _ in _PAIRS], "de", min_count=3)
    assert "schuldner" in df
    assert "verzug" in df
    # Stopword-only / rare grams must be excluded.
    assert "der" not in df
    assert "katze" not in df  # appears once -> below min_count
    assert extract_candidates is candidate_terms


def test_mine_pairs_recovers_legal_pairs() -> None:
    cands = mine_pairs(_tus(), "de", "fr", min_count=3, min_support=3, min_score=0.34)
    pairs = {(c.src, c.tgt) for c in cands}
    assert ("schuldner", "débiteur") in pairs
    assert ("verzug", "demeure") in pairs
    # Noise pair must not surface.
    assert all("katze" not in s for s, _ in pairs)


def test_mine_pairs_carries_evidence_and_score() -> None:
    cands = mine_pairs(_tus(), "de", "fr")
    c = next(c for c in cands if c.src == "verzug")
    assert isinstance(c, TermCandidate)
    assert 0.0 < c.score <= 1.0
    assert c.support >= 3
    assert c.evidence and str(c.evidence[0].uri).startswith("https://www.fedlex.admin.ch")
    assert c.in_termdat is None  # offline: unknown until checked


def test_mine_pairs_handles_reversed_orientation() -> None:
    # Build the same corpus but stored fr->de; mining de->fr must still work.
    reversed_tus = [
        TranslationUnit(
            tu_id=tu.tu_id,
            src_lang="fr",
            tgt_lang="de",
            src=tu.tgt,
            tgt=tu.src,
            source=tu.source,
            alignment=tu.alignment,
        )
        for tu in _tus()
    ]
    cands = mine_pairs(reversed_tus, "de", "fr")
    assert ("schuldner", "débiteur") in {(c.src, c.tgt) for c in cands}


def test_verify_supported_and_unsupported() -> None:
    tus = _tus()
    good = TermCandidate(
        src_lang="de", tgt_lang="fr", src="Verzug", tgt="demeure", score=0.9, support=1
    )
    supported, evidence = verify(good, tus)
    assert supported and evidence

    fabricated = TermCandidate(
        src_lang="de", tgt_lang="fr", src="Verzug", tgt="inexistant", score=0.9, support=1
    )
    supported, evidence = verify(fabricated, tus)
    assert not supported and not evidence
