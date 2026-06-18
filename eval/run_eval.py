"""Reproducible term-grounding evaluation (P7).

Measures **term hit-rate@k**: for each held-out query, does the expected official
target term appear in the target side of the top-k segments retrieved by
``search_parallel``? We compare grounding conditions:

* ``no-grounding`` — floor: no resource at all (does the source query already
  contain the target-language term? ~0 across languages).
* ``lexical`` — OpenGlossa lexical RAG over the official TM.
* ``vector:hashing`` — semantic RAG with the deterministic hashing encoder
  (offline/CI-reproducible).
* ``vector:labse`` — semantic RAG with the production LaBSE encoder
  (requires the ``ml`` extra + model download).

This is the reproducible proxy for "terminological precision with vs without
OpenGlossa grounding". A full MT A/B (COMET/BLEU) is the optional extension.

Run:  python eval/run_eval.py --k 3 --encoders no-grounding lexical vector:hashing
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

# Allow running as a script (python eval/run_eval.py) without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from openglossa.mcp.server import Repository, search_parallel  # noqa: E402
from openglossa.schemas import TranslationUnit  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_CORPUS = EVAL_DIR / "data" / "corpus.jsonl"
DEFAULT_GOLD = EVAL_DIR / "data" / "gold.jsonl"
DEFAULT_RESULTS = EVAL_DIR / "results" / "baseline.json"


def load_corpus(path: Path) -> list[TranslationUnit]:
    return [
        TranslationUnit.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_gold(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _predict(condition: str, repo: Repository, gold: list[dict], k: int, index) -> list[str]:
    """Return one prediction string per gold item for a condition."""
    preds: list[str] = []
    for g in gold:
        if condition == "no-grounding":
            preds.append(g["query"])
            continue
        out = search_parallel(
            repo, g["query"], g["src_lang"], g["tgt_lang"], k=k, index=index
        )
        preds.append(" \u2016 ".join(h["tgt"] for h in out["results"]))
    return preds


def _term_hits(preds: list[str], gold: list[dict]) -> list[bool]:
    return [g["expected"].casefold() in p.casefold() for p, g in zip(preds, gold, strict=True)]


def evaluate(
    corpus: list[TranslationUnit],
    gold: list[dict],
    *,
    k: int = 3,
    conditions: tuple[str, ...] = ("no-grounding", "lexical", "vector:hashing"),
) -> dict:
    """Run all conditions and return a results dict with per-condition hit-rates."""
    repo = Repository()
    repo.tus = corpus

    results: dict = {"k": k, "n": len(gold), "conditions": {}}
    tmpdir = tempfile.mkdtemp(prefix="openglossa-eval-")

    for cond in conditions:
        index = None
        if cond.startswith("vector:"):
            from openglossa.search import HashingEncoder, VectorIndex, load_labse

            kind = cond.split(":", 1)[1]
            encoder = load_labse() if kind == "labse" else HashingEncoder()
            index = VectorIndex.build(corpus, encoder, Path(tmpdir) / f"{kind}.db")

        preds = _predict(cond, repo, gold, k, index)
        hits = _term_hits(preds, gold)
        if index is not None:
            index.close()
        results["conditions"][cond] = {
            "term_hit_rate": round(sum(hits) / len(hits), 4) if hits else 0.0,
            "hits": sum(hits),
            "misses": [g["expected"] for g, h in zip(gold, hits, strict=True) if not h],
        }
    return results


def _print_table(results: dict) -> None:
    print(f"\nterm hit-rate@{results['k']}  (n={results['n']} held-out queries)")
    print("-" * 52)
    for cond, r in results["conditions"].items():
        bar = "#" * round(r["term_hit_rate"] * 20)
        print(f"  {cond:18s} {r['term_hit_rate']:.3f}  {bar}")
    print("-" * 52)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    parser.add_argument("--gold", default=str(DEFAULT_GOLD))
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument(
        "--encoders",
        nargs="*",
        default=["no-grounding", "lexical", "vector:hashing"],
        help="Conditions: no-grounding, lexical, vector:hashing, vector:labse.",
    )
    parser.add_argument("--out", default=str(DEFAULT_RESULTS))
    args = parser.parse_args(argv)

    corpus = load_corpus(Path(args.corpus))
    gold = load_gold(Path(args.gold))
    results = evaluate(corpus, gold, k=args.k, conditions=tuple(args.encoders))
    results["corpus_size"] = len(corpus)

    _print_table(results)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
