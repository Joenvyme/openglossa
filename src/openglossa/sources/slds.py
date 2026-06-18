"""SLDS connector — Swiss Leading Decision Summarization (``ipst/slds``).

Trilingual *regeste* (headnotes) of Federal Supreme Court leading decisions,
1954–2024. License: ✅ VERT (CC-BY-4.0).

Real schema (per row): ``decision_id`` (ATF/BGE citation, e.g. ``"80 I 1"``),
``decision``/``decision_language`` (the judgment text + its original language),
``headnote``/``headnote_language`` (the official summary, published in DE/FR/IT),
``law_area``, ``year``, ``volume``, ``url`` (citable bger.ch link).

The official regeste is published in all three languages, so the parallel pairs
are obtained by **grouping rows by ``decision_id``** and pairing the ``headnote``
text across ``headnote_language``. This produces concept-aligned TM units
(method ``manual`` — professionally translated official text).

The ``datasets`` dependency is optional (``pip install 'openglossa[sources]'``).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Iterator
from itertools import combinations

from openglossa.schemas import Alignment, AlignmentMethod, Lang, SourceRef, TranslationUnit

DATASET_ID = "ipst/slds"
DEFAULT_CONFIG = "default"
SOURCE_NAME = "SLDS"
LICENSE_TAG = "CC-BY-4.0"
BASE_URI = "https://huggingface.co/datasets/ipst/slds"

CORE_LANGS = ("de", "fr", "it")


def _tu_id(decision_id: str, src_lang: str, tgt_lang: str) -> str:
    digest = hashlib.sha1(f"{decision_id}|{src_lang}|{tgt_lang}".encode()).hexdigest()[:16]
    return f"og:tu:{digest}"


def _clean(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def rows_to_translation_units(
    rows: Iterable[dict],
    *,
    langs: tuple[str, ...] = CORE_LANGS,
) -> Iterator[TranslationUnit]:
    """Group rows by ``decision_id`` and emit parallel regeste TUs per language pair.

    Deduplication is implicit: one headnote per (decision_id, language) is kept,
    and each (decision_id, src, tgt) yields a single TU.
    """
    groups: dict[str, dict] = {}
    order: list[str] = []
    for row in rows:
        decision_id = _clean(row.get("decision_id"))
        hn_lang = _clean(row.get("headnote_language"))
        headnote = _clean(row.get("headnote"))
        if not decision_id or hn_lang not in langs or not headnote:
            continue
        group = groups.get(decision_id)
        if group is None:
            group = {
                "texts": {},
                "url": _clean(row.get("url")) or BASE_URI,
                "law_area": _clean(row.get("law_area")),
            }
            groups[decision_id] = group
            order.append(decision_id)
        group["texts"].setdefault(hn_lang, headnote)

    for decision_id in order:
        group = groups[decision_id]
        texts: dict[str, str] = group["texts"]
        domain = [group["law_area"]] if group["law_area"] else []
        for src_lang, tgt_lang in combinations(langs, 2):
            src = texts.get(src_lang)
            tgt = texts.get(tgt_lang)
            if not src or not tgt:
                continue
            yield TranslationUnit(
                tu_id=_tu_id(decision_id, src_lang, tgt_lang),
                src_lang=Lang(src_lang),
                tgt_lang=Lang(tgt_lang),
                src=src,
                tgt=tgt,
                domain=domain,
                source=SourceRef(
                    name=SOURCE_NAME,
                    uri=group["url"],  # type: ignore[arg-type]
                    license=LICENSE_TAG,
                    ref=f"ATF {decision_id}",
                ),
                alignment=Alignment(method=AlignmentMethod.manual, score=1.0),
            )


def load_translation_units(
    *,
    split: str = "train",
    config: str = DEFAULT_CONFIG,
    langs: tuple[str, ...] = CORE_LANGS,
    limit: int | None = None,
) -> Iterator[TranslationUnit]:
    """Load ``ipst/slds`` from the Hugging Face Hub and yield regeste TUs.

    Parameters
    ----------
    limit:
        Max number of distinct decisions to ingest (``None`` = all). Rows are
        streamed and grouped by ``decision_id``.

    Raises
    ------
    ImportError
        If the optional ``sources`` extra (``datasets``) is not installed.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "load_translation_units requires the 'sources' extra: "
            "pip install 'openglossa[sources]'"
        ) from exc

    ds = load_dataset(DATASET_ID, config, split=split, streaming=True)

    rows: list[dict] = []
    seen_ids: set[str] = set()
    for row in ds:
        decision_id = row.get("decision_id")
        if limit is not None and decision_id not in seen_ids and len(seen_ids) >= limit:
            break
        if decision_id is not None:
            seen_ids.add(decision_id)
        rows.append(dict(row))

    yield from rows_to_translation_units(rows, langs=langs)


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    for tu in load_translation_units(limit=3):
        print(f"[{tu.src_lang}->{tu.tgt_lang}] {tu.source.ref}: {tu.src[:50]} || {tu.tgt[:50]}")
