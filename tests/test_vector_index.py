from __future__ import annotations

import pytest

from openglossa.mcp.server import Repository, search_parallel
from openglossa.schemas import Alignment, AlignmentMethod, SourceRef, TranslationUnit
from openglossa.search import HashingEncoder, VectorIndex

_PAIRS = [
    ("Der Schuldner kommt in Verzug.", "Le débiteur est en demeure."),
    ("Der Vertrag ist gültig.", "Le contrat est valable."),
    ("Die Katze schläft im Garten.", "Le chat dort dans le jardin."),
]


def _tus() -> list[TranslationUnit]:
    tus = []
    for i, (de, fr) in enumerate(_PAIRS):
        tus.append(
            TranslationUnit(
                tu_id=f"og:tu:vec{i:04d}",
                src_lang="de",
                tgt_lang="fr",
                src=de,
                tgt=fr,
                source=SourceRef(
                    name="Fedlex",
                    uri=f"https://www.fedlex.admin.ch/eli/cc/x/de#art_{i}",
                    license="Fedlex-open-reuse",
                    ref=f"SR 220 Art. {i + 1}",
                ),
                alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
            )
        )
    return tus


def test_vector_index_build_and_search(tmp_path):
    idx = VectorIndex.build(_tus(), HashingEncoder(), tmp_path / "tm.db")
    hits = idx.search("Schuldner Verzug", "de", "fr", k=2)
    assert hits
    assert hits[0]["src"] == "Der Schuldner kommt in Verzug."
    assert hits[0]["tgt"] == "Le débiteur est en demeure."
    assert hits[0]["source"]["ref"] == "SR 220 Art. 1"
    assert 0.0 <= hits[0]["score"] <= 1.0
    idx.close()


def test_vector_index_direction_agnostic(tmp_path):
    idx = VectorIndex.build(_tus(), HashingEncoder(), tmp_path / "tm.db")
    # Query in FR -> expect the DE counterpart back.
    hits = idx.search("contrat valable", "fr", "de", k=1)
    assert hits
    assert hits[0]["src"] == "Le contrat est valable."
    assert hits[0]["tgt"] == "Der Vertrag ist gültig."
    idx.close()


def test_open_validates_encoder(tmp_path):
    VectorIndex.build(_tus(), HashingEncoder(dim=256), tmp_path / "tm.db").close()
    VectorIndex.open(tmp_path / "tm.db", HashingEncoder(dim=256)).close()
    with pytest.raises(ValueError):
        VectorIndex.open(tmp_path / "tm.db", HashingEncoder(dim=128))


def test_search_parallel_uses_index_and_reports_method(tmp_path):
    idx = VectorIndex.build(_tus(), HashingEncoder(), tmp_path / "tm.db")
    repo = Repository()  # empty repo: results must come from the index
    out = search_parallel(repo, "Schuldner Verzug", "de", "fr", k=2, index=idx)
    assert out["method"] == "vector"
    assert out["results"][0]["tgt"] == "Le débiteur est en demeure."
    idx.close()


def test_search_parallel_falls_back_to_lexical_on_index_error():
    class Boom:
        def search(self, *a, **k):
            raise RuntimeError("index unavailable")

    repo = Repository()
    repo.tus = _tus()
    out = search_parallel(repo, "Schuldner Verzug", "de", "fr", k=2, index=Boom())
    assert out["method"] == "lexical"
    assert out["vector_error"] == "index unavailable"
    assert out["results"]
