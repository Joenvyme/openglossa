from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from openglossa.schemas import Alignment, AlignmentMethod, SourceRef, TranslationUnit

_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


run_eval = _load("og_run_eval", "eval/run_eval.py")
metric = _load("og_term_hit_rate", "eval/term_hit_rate.py")


def _corpus() -> list[TranslationUnit]:
    data = [
        ("Der Schuldner kommt in Verzug.", "Le débiteur est en demeure.", "SR 220 Art. 102"),
        ("Der Vertrag ist gültig.", "Le contrat est valable.", "SR 220 Art. 1"),
    ]
    out = []
    for i, (de, fr, ref) in enumerate(data):
        out.append(
            TranslationUnit(
                tu_id=f"og:tu:ev{i:04d}",
                src_lang="de",
                tgt_lang="fr",
                src=de,
                tgt=fr,
                source=SourceRef(
                    name="Fedlex",
                    uri=f"https://www.fedlex.admin.ch/eli/cc/x/de#art_{i}",
                    license="Fedlex-open-reuse",
                    ref=ref,
                ),
                alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
            )
        )
    return out


_GOLD = [
    {"src_lang": "de", "tgt_lang": "fr", "query": "Der Schuldner zahlt zu spät.", "expected": "demeure"},
]


def test_term_hit_rate_metric():
    assert metric.term_hit_rate(["Le débiteur est en demeure."], ["demeure"]) == 1.0
    assert metric.term_hit_rate(["Le contrat est valable."], ["demeure"]) == 0.0
    with pytest.raises(ValueError):
        metric.term_hit_rate(["a", "b"], ["a"])


def test_evaluate_grounding_beats_no_grounding():
    res = run_eval.evaluate(
        _corpus(),
        _GOLD,
        k=2,
        conditions=("no-grounding", "lexical", "vector:hashing"),
    )
    conds = res["conditions"]
    assert conds["no-grounding"]["term_hit_rate"] == 0.0
    assert conds["lexical"]["term_hit_rate"] == 1.0
    assert conds["vector:hashing"]["term_hit_rate"] == 1.0
    assert res["n"] == 1


def test_real_gold_set_is_well_formed():
    gold = run_eval.load_gold(run_eval.DEFAULT_GOLD)
    assert len(gold) >= 10
    for g in gold:
        assert {"src_lang", "tgt_lang", "query", "expected", "ref"} <= set(g)
