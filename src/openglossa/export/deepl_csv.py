"""DeepL glossary CSV export.

DeepL expects a headerless CSV with one ``source,target`` pair per line, for a
single language direction. We derive pairs from the preferred terms of each
:class:`~openglossa.schemas.TermRecord`.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from openglossa.schemas import TermRecord


def deepl_pairs(
    records: Iterable[TermRecord],
    src_lang: str,
    tgt_lang: str,
) -> list[tuple[str, str]]:
    """Extract (source, target) preferred-term pairs for a language direction."""
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for rec in records:
        src = rec.preferred(src_lang)
        tgt = rec.preferred(tgt_lang)
        if not src or not tgt:
            continue
        key = (src, tgt)
        if key in seen:
            continue
        seen.add(key)
        pairs.append(key)
    return pairs


def write_deepl_glossary(
    records: Iterable[TermRecord],
    src_lang: str,
    tgt_lang: str,
    path: str | Path,
) -> Path:
    """Write a DeepL-compatible glossary CSV. Returns the written path."""
    pairs = deepl_pairs(records, src_lang, tgt_lang)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerows(pairs)
    return out
