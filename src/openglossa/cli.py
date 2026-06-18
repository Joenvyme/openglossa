"""OpenGlossa command-line pipeline.

Commands
--------
ingest-fedlex   Fetch consolidated acts from Fedlex (live SPARQL) and write
                title-level parallel TranslationUnits to data/processed/tus.jsonl.
mine-terms      Mine source→target term candidates from parallel TUs by
                co-occurrence (Dice) and write a human-review queue (JSONL).
build-index     Build a sqlite-vec semantic index over the TM (search_parallel).
build-exports   Read data/processed/*.jsonl and write all export formats
                (TBX, TMX, DeepL CSV per language pair, JSONL copies).
poc             ingest-fedlex on a default set of core acts, then build-exports.

Run:  python -m openglossa <command> [options]
"""

from __future__ import annotations

import argparse
import sys
from itertools import combinations
from pathlib import Path

from openglossa import CORE_LANGUAGES
from openglossa.export import (
    TBX_DTD,
    TMX_DTD,
    read_jsonl,
    validate_tbx,
    validate_tmx,
    validate_with_dtd,
    write_deepl_glossary,
    write_jsonl,
    write_parquet,
    write_tbx,
    write_tmx,
)
from openglossa.schemas import Lang, TermRecord, TranslationUnit

# A handful of core federal acts for the PoC slice (RS numbers).
DEFAULT_POC_ACTS = [
    "101",  # Bundesverfassung / Constitution fédérale / Costituzione federale
    "210",  # ZGB / Code civil / Codice civile
    "220",  # OR / Code des obligations / Codice delle obbligazioni
    "311.0",  # StGB / Code pénal / Codice penale
    "312.0",  # StPO / Code de procédure pénale / Codice di procedura penale
]

PROCESSED = Path("data/processed")
EXPORTS = Path("data/exports")


def cmd_ingest_fedlex(args: argparse.Namespace) -> int:
    from openglossa.sources import fedlex

    out_path = Path(args.out)
    rs_numbers: list[str] = args.rs or (["220"] if args.articles else DEFAULT_POC_ACTS)
    langs = tuple(args.langs)
    kind = "article/alinéa" if args.articles else "title"

    all_units: list[TranslationUnit] = []
    for rs in rs_numbers:
        try:
            if args.articles:
                units = fedlex.fetch_article_translation_units(
                    rs, langs=langs, limit=args.max_articles
                )
            else:
                units = fedlex.fetch_title_translation_units(rs, langs=langs)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! RS {rs}: {exc}", file=sys.stderr)
            continue
        print(f"  RS {rs}: {len(units)} {kind} TU(s)")
        all_units.extend(units)

    write_jsonl(all_units, out_path)
    print(f"wrote {len(all_units)} translation units -> {out_path}")
    return 0


def cmd_ingest_slds(args: argparse.Namespace) -> int:
    from openglossa.sources import slds

    out_path = Path(args.out)
    langs = tuple(args.langs)
    limit = args.limit if args.limit and args.limit > 0 else None

    units = list(slds.load_translation_units(split=args.split, langs=langs, limit=limit))
    write_jsonl(units, out_path)
    print(f"wrote {len(units)} regeste translation units -> {out_path}")
    return 0


def _merge_jsonl(paths: list[Path], out_path: Path) -> int:
    """Concatenate JSONL files into one, de-duplicating TUs by tu_id."""
    seen: set[str] = set()
    lines: list[str] = []
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            tu = TranslationUnit.model_validate_json(line)
            if tu.tu_id in seen:
                continue
            seen.add(tu.tu_id)
            lines.append(line)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def cmd_merge_tus(args: argparse.Namespace) -> int:
    n = _merge_jsonl([Path(p) for p in args.inputs], Path(args.out))
    print(f"merged {len(args.inputs)} file(s) -> {n} unique TUs -> {args.out}")
    return 0


def cmd_ingest_termdat(args: argparse.Namespace) -> int:
    """Look up terms in TERMDAT (live) and persist a redistribution-safe derived
    index only (concept_id + URI + identifier + languages + legal basis).

    Honours hard rule #6: TERMDAT redistribution is unconfirmed, so raw term text
    is never written to disk here. Use the MCP server for live term text.
    """
    import json

    from openglossa.sources import termdat

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for term in args.terms:
            try:
                derived = termdat.derived_index(term, args.src, limit=args.limit)
            except Exception as exc:  # noqa: BLE001
                print(f"  ! '{term}': {exc}", file=sys.stderr)
                continue
            print(f"  '{term}' ({args.src}): {len(derived)} entr(y/ies)")
            for d in derived:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} derived TERMDAT records (no raw text, rule #6) -> {out_path}")
    return 0


def _termdat_has_pair(src: str, tgt: str, src_lang: str, tgt_lang: str, limit: int) -> bool:
    """Best-effort live check: is the (src, tgt) pair already known in TERMDAT?"""
    from openglossa.sources import termdat

    records = termdat.lookup_live(src, src_lang, langs=(src_lang, tgt_lang), limit=limit)
    tgt_cf = tgt.casefold()
    for rec in records:
        tgt_terms = rec.terms.get(tgt_lang) or rec.terms.get(Lang(tgt_lang)) or []
        for term in tgt_terms:
            text_cf = term.text.casefold()
            if tgt_cf in text_cf or text_cf in tgt_cf:
                return True
    return False


def cmd_mine_terms(args: argparse.Namespace) -> int:
    """Mine source→target term candidates from parallel TUs (P4 review queue)."""
    from openglossa.mining import mine_pairs

    src = Lang(args.src)
    tgt = Lang(args.tgt)
    tus = read_jsonl(TranslationUnit, Path(args.input))
    if not tus:
        print(f"no translation units in {args.input} — run 'ingest-fedlex' first", file=sys.stderr)
        return 1

    candidates = mine_pairs(
        tus,
        src,
        tgt,
        min_count=args.min_count,
        min_support=args.min_support,
        min_score=args.min_score,
    )
    print(f"mined {len(candidates)} candidate pair(s) {src}->{tgt} from {len(tus)} TUs")

    if args.check_termdat:
        kept: list = []
        for c in candidates:
            try:
                known = _termdat_has_pair(c.src, c.tgt, args.src, args.tgt, args.limit)
            except Exception as exc:  # noqa: BLE001
                print(f"  ! termdat check '{c.src}': {exc}", file=sys.stderr)
                known = None
            c.in_termdat = known
            if args.novel_only and known:
                continue
            kept.append(c)
        if args.novel_only:
            print(f"  kept {len(kept)} candidate(s) absent from TERMDAT")
        candidates = kept

    write_jsonl(candidates, Path(args.out))
    print(f"wrote {len(candidates)} candidates -> {args.out}")
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    """Build a sqlite-vec semantic index over the TM for search_parallel."""
    from openglossa.search import HashingEncoder, VectorIndex, load_labse

    tus = read_jsonl(TranslationUnit, Path(args.input))
    if not tus:
        print(f"no translation units in {args.input} — run 'ingest-fedlex' first", file=sys.stderr)
        return 1

    if args.encoder == "labse":
        print("loading LaBSE (first run downloads the model)…")
        encoder = load_labse()
    else:
        encoder = HashingEncoder()
    print(f"encoding {len(tus)} TUs (2 sides each) with {encoder.name} (dim={encoder.dim})…")

    index = VectorIndex.build(tus, encoder, Path(args.out))
    index.close()
    print(f"wrote vector index -> {args.out}")
    return 0


def cmd_build_exports(args: argparse.Namespace) -> int:
    processed = Path(args.processed)
    exports = Path(args.out)
    exports.mkdir(parents=True, exist_ok=True)

    terms = read_jsonl(TermRecord, processed / "terms.jsonl")
    tus = read_jsonl(TranslationUnit, processed / "tus.jsonl")
    print(f"loaded {len(terms)} term records, {len(tus)} translation units")

    written: list[Path] = []
    to_validate: list[tuple[Path, str]] = []

    def _maybe_parquet(records, path: Path) -> None:
        try:
            written.append(write_parquet(records, path))
        except ImportError as exc:
            print(f"  (skipping {path.name}: {exc})")

    if tus:
        tmx = write_tmx(tus, exports / "openglossa.tmx")
        written.append(tmx)
        to_validate.append((tmx, "tmx"))
        written.append(write_jsonl(tus, exports / "tus.jsonl"))
        _maybe_parquet(tus, exports / "tus.parquet")
    if terms:
        tbx = write_tbx(terms, exports / "openglossa.tbx")
        written.append(tbx)
        to_validate.append((tbx, "tbx"))
        written.append(write_jsonl(terms, exports / "terms.jsonl"))
        _maybe_parquet(terms, exports / "terms.parquet")
        for src, tgt in combinations(CORE_LANGUAGES, 2):
            path = exports / f"glossary_deepl_{src}-{tgt}.csv"
            written.append(write_deepl_glossary(terms, src, tgt, path))

    for p in written:
        print(f"  wrote {p}")
    if not written:
        print("nothing to export (data/processed is empty) — run 'ingest-fedlex' first")
        return 0

    problems = 0
    for path, kind in to_validate:
        structural = validate_tmx(path) if kind == "tmx" else validate_tbx(path)
        try:
            dtd = validate_with_dtd(path, TMX_DTD if kind == "tmx" else TBX_DTD)
            checks = "structural + DTD"
        except ImportError:
            dtd = []
            checks = "structural (DTD skipped: install 'sources' extra)"
        issues = structural + dtd
        if issues:
            problems += len(issues)
            print(f"  ! {path.name} INVALID:")
            for msg in issues:
                print(f"      - {msg}")
        else:
            print(f"  validated {path.name} ({checks})")
    return 1 if problems else 0


def cmd_poc(args: argparse.Namespace) -> int:
    ingest_args = argparse.Namespace(
        rs=None, langs=list(CORE_LANGUAGES), out=str(PROCESSED / "tus.jsonl")
    )
    rc = cmd_ingest_fedlex(ingest_args)
    if rc != 0:
        return rc
    return cmd_build_exports(
        argparse.Namespace(processed=str(PROCESSED), out=str(EXPORTS))
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openglossa", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_ing = sub.add_parser("ingest-fedlex", help="Fetch Fedlex acts -> parallel TUs (JSONL).")
    p_ing.add_argument("--rs", nargs="*", help="RS numbers (default: PoC core acts).")
    p_ing.add_argument("--langs", nargs="*", default=list(CORE_LANGUAGES), help="Languages.")
    p_ing.add_argument(
        "--articles",
        action="store_true",
        help="Article/alinéa-level alignment (Akoma Ntoso eId) instead of titles.",
    )
    p_ing.add_argument(
        "--max-articles",
        type=int,
        default=0,
        help="Limit aligned eIds per act (0 = all). Useful for a verifiable slice.",
    )
    p_ing.add_argument("--out", default=str(PROCESSED / "tus.jsonl"), help="Output JSONL path.")
    p_ing.set_defaults(func=cmd_ingest_fedlex)

    p_slds = sub.add_parser("ingest-slds", help="Fetch SLDS regeste -> trilingual TUs (JSONL).")
    p_slds.add_argument("--langs", nargs="*", default=list(CORE_LANGUAGES), help="Languages.")
    p_slds.add_argument("--split", default="train", help="Dataset split (default: train).")
    p_slds.add_argument(
        "--limit", type=int, default=0, help="Max distinct decisions (0 = all)."
    )
    p_slds.add_argument("--out", default=str(PROCESSED / "tus_slds.jsonl"), help="Output JSONL.")
    p_slds.set_defaults(func=cmd_ingest_slds)

    p_td = sub.add_parser(
        "ingest-termdat",
        help="Live TERMDAT lookup -> derived index only (rule #6, no raw text).",
    )
    p_td.add_argument("terms", nargs="+", help="Source-language terms to look up.")
    p_td.add_argument("--src", default="de", help="Source language (default: de).")
    p_td.add_argument("--limit", type=int, default=10, help="Max entries per term.")
    p_td.add_argument(
        "--out", default=str(PROCESSED / "termdat_derived.jsonl"), help="Output JSONL."
    )
    p_td.set_defaults(func=cmd_ingest_termdat)

    p_merge = sub.add_parser("merge-tus", help="Merge JSONL TU files, dedup by tu_id.")
    p_merge.add_argument("inputs", nargs="+", help="Input JSONL files.")
    p_merge.add_argument("--out", default=str(PROCESSED / "tus.jsonl"), help="Output JSONL.")
    p_merge.set_defaults(func=cmd_merge_tus)

    p_mine = sub.add_parser(
        "mine-terms",
        help="Mine term candidates from parallel TUs (co-occurrence Dice) -> review queue.",
    )
    p_mine.add_argument(
        "--in", dest="input", default=str(PROCESSED / "tus.jsonl"), help="Input TUs."
    )
    p_mine.add_argument("--src", default="de", help="Source language (default: de).")
    p_mine.add_argument("--tgt", default="fr", help="Target language (default: fr).")
    p_mine.add_argument("--min-count", type=int, default=3, help="Min term doc-frequency.")
    p_mine.add_argument("--min-support", type=int, default=3, help="Min pair co-occurrence.")
    p_mine.add_argument("--min-score", type=float, default=0.34, help="Min Dice score.")
    p_mine.add_argument(
        "--check-termdat",
        action="store_true",
        help="Flag pairs already known in TERMDAT (live SPARQL, network).",
    )
    p_mine.add_argument(
        "--novel-only",
        action="store_true",
        help="With --check-termdat: keep only pairs absent from TERMDAT.",
    )
    p_mine.add_argument("--limit", type=int, default=10, help="TERMDAT lookup limit per term.")
    p_mine.add_argument(
        "--out", default=str(PROCESSED / "term_candidates.jsonl"), help="Output JSONL."
    )
    p_mine.set_defaults(func=cmd_mine_terms)

    p_idx = sub.add_parser(
        "build-index",
        help="Build a sqlite-vec semantic index over the TM (for search_parallel).",
    )
    p_idx.add_argument(
        "--in", dest="input", default=str(PROCESSED / "tus.jsonl"), help="Input TUs."
    )
    p_idx.add_argument(
        "--encoder",
        choices=["labse", "hashing"],
        default="labse",
        help="Embedding encoder (labse = production; hashing = light, offline).",
    )
    p_idx.add_argument(
        "--out", default=str(PROCESSED / "tm_index.db"), help="Output sqlite-vec index path."
    )
    p_idx.set_defaults(func=cmd_build_index)

    p_exp = sub.add_parser("build-exports", help="Write all export formats from data/processed.")
    p_exp.add_argument("--processed", default=str(PROCESSED), help="Processed JSONL dir.")
    p_exp.add_argument("--out", default=str(EXPORTS), help="Exports output dir.")
    p_exp.set_defaults(func=cmd_build_exports)

    p_poc = sub.add_parser("poc", help="End-to-end PoC: ingest core acts + build exports.")
    p_poc.set_defaults(func=cmd_poc)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
