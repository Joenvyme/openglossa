"""SLDS connector — Swiss Leading Decision Summarization (``ipst/slds``).

Trilingual regeste (headnotes) of Federal Supreme Court decisions, 1954–2024.
License: ✅ VERT (CC-BY-4.0). This builds :class:`TranslationUnit` records by
pairing the language fields of each decision (DE↔FR, DE↔IT, FR↔IT).

The ``datasets`` dependency is optional (``pip install 'openglossa[sources]'``).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Iterator
from itertools import combinations

from openglossa.schemas import Alignment, AlignmentMethod, Lang, SourceRef, TranslationUnit

DATASET_ID = "ipst/slds"
SOURCE_NAME = "SLDS"
LICENSE_TAG = "CC-BY-4.0"
BASE_URI = "https://huggingface.co/datasets/ipst/slds"

CORE_LANGS = ("de", "fr", "it")

# Candidate field names per language in the upstream dataset. The exact schema may
# evolve; we probe several conventional names and use the first present.
_LANG_FIELDS: dict[str, tuple[str, ...]] = {
    "de": ("regeste_de", "headnote_de", "de", "text_de"),
    "fr": ("regeste_fr", "headnote_fr", "fr", "text_fr"),
    "it": ("regeste_it", "headnote_it", "it", "text_it"),
}
# Candidate field names for the decision reference (e.g. BGE/ATF citation).
_REF_FIELDS = ("bge", "atf", "citation", "reference", "decision_id", "id")


def _tu_id(src: str, tgt: str, src_lang: str, tgt_lang: str) -> str:
    digest = hashlib.sha1(f"{src_lang}|{tgt_lang}|{src}|{tgt}".encode()).hexdigest()[:16]
    return f"og:tu:{digest}"


def _first_present(row: dict, candidates: Iterable[str]) -> str | None:
    for key in candidates:
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def rows_to_translation_units(
    rows: Iterable[dict],
    *,
    langs: tuple[str, ...] = CORE_LANGS,
) -> Iterator[TranslationUnit]:
    """Convert raw dataset rows into deduplicated parallel :class:`TranslationUnit`.

    For each row, every available language pair produces one TU (both directions
    are represented by emitting the ordered pair as-is from ``combinations``).
    Deduplication is by content hash.
    """
    seen: set[str] = set()
    for row in rows:
        ref = _first_present(row, _REF_FIELDS)
        texts = {lang: _first_present(row, _LANG_FIELDS.get(lang, ())) for lang in langs}

        for src_lang, tgt_lang in combinations(langs, 2):
            src = texts.get(src_lang)
            tgt = texts.get(tgt_lang)
            if not src or not tgt:
                continue
            tu_id = _tu_id(src, tgt, src_lang, tgt_lang)
            if tu_id in seen:
                continue
            seen.add(tu_id)

            yield TranslationUnit(
                tu_id=tu_id,
                src_lang=Lang(src_lang),
                tgt_lang=Lang(tgt_lang),
                src=src,
                tgt=tgt,
                source=SourceRef(
                    name=SOURCE_NAME,
                    uri=BASE_URI,  # type: ignore[arg-type]
                    license=LICENSE_TAG,
                    ref=ref,
                ),
                alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
            )


def load_translation_units(
    *,
    split: str = "train",
    langs: tuple[str, ...] = CORE_LANGS,
    limit: int | None = None,
) -> Iterator[TranslationUnit]:
    """Load ``ipst/slds`` from the Hugging Face Hub and yield TUs.

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

    ds = load_dataset(DATASET_ID, split=split, streaming=limit is not None)

    def _rows() -> Iterator[dict]:
        for i, row in enumerate(ds):
            if limit is not None and i >= limit:
                break
            yield dict(row)

    yield from rows_to_translation_units(_rows(), langs=langs)


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    for tu in load_translation_units(limit=5):
        print(f"[{tu.src_lang}->{tu.tgt_lang}] {tu.src[:60]} || {tu.tgt[:60]}")
