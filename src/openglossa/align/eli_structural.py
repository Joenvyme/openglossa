"""ELI/eId structural alignment.

Given per-language segment maps (``eId -> text``) parsed from Fedlex Akoma Ntoso
manifestations of the *same* act, pair segments that share an ``eId`` across
languages. The shared ``eId`` is an exact structural anchor, so the alignment is
high-confidence (score 1.0) — this is the core of OpenGlossa's "citable by
construction" promise.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from itertools import combinations

from openglossa.schemas import (
    Alignment,
    AlignmentMethod,
    Lang,
    SourceRef,
    TranslationUnit,
)
from openglossa.sources.akn import ref_from_eid

SOURCE_NAME = "Fedlex"
LICENSE_TAG = "Fedlex-open-reuse"


def _tu_id(rs: str, eid: str, src_lang: str, tgt_lang: str) -> str:
    digest = hashlib.sha1(f"{rs}|{eid}|{src_lang}|{tgt_lang}".encode()).hexdigest()[:16]
    return f"og:tu:{digest}"


def shared_eids(
    segments_by_lang: Mapping[str, Mapping[str, str]],
    langs: Sequence[str],
) -> list[str]:
    """eIds present (and non-empty) in every requested language, order-preserved."""
    present = [set(segments_by_lang.get(lang, {})) for lang in langs]
    if not present:
        return []
    common = set.intersection(*present)
    # Preserve the order from the first language's mapping.
    first = segments_by_lang.get(langs[0], {})
    return [eid for eid in first if eid in common]


def align_segments(
    rs_number: str,
    segments_by_lang: Mapping[str, Mapping[str, str]],
    *,
    langs: Sequence[str],
    citable_uri_by_lang: Mapping[str, str] | None = None,
    domain: Sequence[str] | None = None,
    limit: int = 0,
) -> list[TranslationUnit]:
    """Produce article/alinéa-level parallel TUs for every language pair.

    Parameters
    ----------
    rs_number:
        RS number, used for provenance and citations.
    segments_by_lang:
        ``{lang: {eId: text}}`` from :func:`openglossa.sources.akn.parse_segments`.
    citable_uri_by_lang:
        Citable ELI expression URI per language (used as ``source.uri``). Falls
        back to a generic Fedlex URL if missing.
    limit:
        Max number of eIds to align (0 = all). Useful for verifiable slices.
    """
    domain = list(domain) if domain else ["statute"]
    citable_uri_by_lang = citable_uri_by_lang or {}
    eids = shared_eids(segments_by_lang, langs)
    if limit:
        eids = eids[:limit]

    units: list[TranslationUnit] = []
    for eid in eids:
        ref = ref_from_eid(rs_number, eid)
        for src_lang, tgt_lang in combinations(langs, 2):
            src_text = segments_by_lang[src_lang][eid]
            tgt_text = segments_by_lang[tgt_lang][eid]
            uri = citable_uri_by_lang.get(src_lang) or "https://www.fedlex.admin.ch/"
            units.append(
                TranslationUnit(
                    tu_id=_tu_id(rs_number, eid, src_lang, tgt_lang),
                    src_lang=Lang(src_lang),
                    tgt_lang=Lang(tgt_lang),
                    src=src_text,
                    tgt=tgt_text,
                    domain=domain,
                    source=SourceRef(
                        name=SOURCE_NAME,
                        uri=uri,  # type: ignore[arg-type]
                        license=LICENSE_TAG,
                        ref=ref,
                    ),
                    alignment=Alignment(method=AlignmentMethod.eli_structural, score=1.0),
                )
            )
    return units
