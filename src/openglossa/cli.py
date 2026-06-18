"""OpenGlossa command-line pipeline.

Commands
--------
ingest-fedlex   Fetch consolidated acts from Fedlex (live SPARQL) and write
                title-level parallel TranslationUnits to data/processed/tus.jsonl.
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
    read_jsonl,
    write_deepl_glossary,
    write_jsonl,
    write_tbx,
    write_tmx,
)
from openglossa.schemas import TermRecord, TranslationUnit

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


def cmd_build_exports(args: argparse.Namespace) -> int:
    processed = Path(args.processed)
    exports = Path(args.out)
    exports.mkdir(parents=True, exist_ok=True)

    terms = read_jsonl(TermRecord, processed / "terms.jsonl")
    tus = read_jsonl(TranslationUnit, processed / "tus.jsonl")
    print(f"loaded {len(terms)} term records, {len(tus)} translation units")

    written: list[Path] = []

    if tus:
        written.append(write_tmx(tus, exports / "openglossa.tmx"))
        written.append(write_jsonl(tus, exports / "tus.jsonl"))
    if terms:
        written.append(write_tbx(terms, exports / "openglossa.tbx"))
        written.append(write_jsonl(terms, exports / "terms.jsonl"))
        for src, tgt in combinations(CORE_LANGUAGES, 2):
            path = exports / f"glossary_deepl_{src}-{tgt}.csv"
            written.append(write_deepl_glossary(terms, src, tgt, path))

    for p in written:
        print(f"  wrote {p}")
    if not written:
        print("nothing to export (data/processed is empty) — run 'ingest-fedlex' first")
    return 0


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
