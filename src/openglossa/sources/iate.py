"""IATE connector — EU institutional terminology database (live API).

Status: ✅ GREEN. Reuse is permitted for commercial and non-commercial purposes
under European Commission Decision 2011/833/EU, provided the EU/IATE is cited as
the source (see LICENSING.md). Live queries use the public search API documented
at https://iate.europa.eu/developers — no API key required.

IATE complements Swiss sources (TERMDAT/Fedlex): it covers EU-specific and
general legal terminology in all EU languages including English, but it is **not**
Swiss federal law.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from openglossa.schemas import Authority, ReviewStatus, Term, TermRecord, TermStatus

SEARCH_URL = "https://iate.europa.eu/em-api/entries/_search?expand=true&offset=0&limit={limit}"
ENTRY_URL = "https://iate.europa.eu/entry/result/{entry_id}"
SOURCE_NAME = "IATE"
LICENSE_TAG = "EU-2011/833-reuse"
ATTRIBUTION = "© European Union — IATE (https://iate.europa.eu)"

# Bundling full IATE dumps is allowed with attribution; v1 stays live-only for
# operational simplicity (TBX export can be added later).
REDISTRIBUTION_CONFIRMED = True

CORE_LANGS = ("de", "fr", "it", "en")
SUPPORTED_LANGS = CORE_LANGS + ("rm",)


def assert_redistribution_allowed() -> None:
    """IATE reuse is permitted with attribution (Decision 2011/833/EU)."""
    if not REDISTRIBUTION_CONFIRMED:
        raise PermissionError("IATE redistribution flag is disabled.")


def _reliability_code(term_entry: dict[str, Any]) -> int:
    rel = (term_entry.get("metadata") or {}).get("reliability")
    if isinstance(rel, dict):
        try:
            return int(rel.get("code", 0))
        except (TypeError, ValueError):
            return 0
    if isinstance(rel, int):
        return rel
    return 0


def _is_primary(term_entry: dict[str, Any]) -> bool:
    primary = (term_entry.get("metadata") or {}).get("primary") or {}
    name = primary.get("name") if isinstance(primary, dict) else None
    return name == "primary"


def _post_search(payload: dict[str, Any], *, timeout: int = 30) -> list[dict[str, Any]]:
    url = SEARCH_URL.format(limit=int(payload.get("_limit", 10)))
    body = json.dumps({k: v for k, v in payload.items() if not k.startswith("_")}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OpenGlossa/0.1 (+https://github.com/Joenvyme/openglossa)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"IATE search failed: {exc}") from exc
    items = data.get("items") or []
    return items if isinstance(items, list) else []


def _collect_terms(
    item: dict[str, Any],
    *,
    langs: tuple[str, ...],
) -> dict[str, list[tuple[str, TermStatus, int]]]:
    """Return ``lang -> [(text, status, reliability)]`` sorted best-first per lang."""
    out: dict[str, list[tuple[str, TermStatus, int]]] = {}
    language_blocks = item.get("language") or {}
    for lang, block in language_blocks.items():
        if lang not in langs:
            continue
        scored: list[tuple[str, TermStatus, int]] = []
        for te in block.get("term_entries") or []:
            text = (te.get("term_value") or "").strip()
            if not text:
                continue
            rel = _reliability_code(te)
            status = TermStatus.preferred if _is_primary(te) else TermStatus.admitted
            scored.append((text, status, rel))
        if not scored:
            continue
        scored.sort(key=lambda x: (x[1] != TermStatus.preferred, -x[2], x[0].casefold()))
        out[lang] = scored
    return out


def entry_to_term_record(
    item: dict[str, Any],
    *,
    langs: tuple[str, ...] = CORE_LANGS,
) -> TermRecord | None:
    """Map one expanded IATE search hit to a :class:`TermRecord`."""
    from openglossa.schemas import SourceRef

    entry_id = item.get("id")
    if entry_id is None:
        return None
    collected = _collect_terms(item, langs=langs)
    terms: dict[str, list[Term]] = {}
    for lang, scored in collected.items():
        bucket: list[Term] = []
        seen: set[str] = set()
        for text, status, _rel in scored:
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            # First term in sorted list becomes preferred if none marked primary.
            if bucket and status == TermStatus.preferred:
                bucket.append(Term(text=text, status=status))
            elif not bucket:
                bucket.append(Term(text=text, status=TermStatus.preferred))
            else:
                bucket.append(Term(text=text, status=TermStatus.admitted))
        if bucket:
            terms[lang] = bucket
    if not terms:
        return None

    # Definition: first language-level note in any requested language.
    definition: dict[str, str] = {}
    for lang, block in (item.get("language") or {}).items():
        if lang not in langs:
            continue
        note = block.get("note") or {}
        val = note.get("value") or note.get("tooltip_value")
        if val and lang not in definition:
            definition[lang] = str(val).strip()

    return TermRecord(
        concept_id=f"og:term:iate-{entry_id}",
        definition=definition,
        terms=terms,
        authority=Authority.administrative,
        sources=[
            SourceRef(
                name=SOURCE_NAME,
                uri=ENTRY_URL.format(entry_id=entry_id),  # type: ignore[arg-type]
                license=LICENSE_TAG,
                ref=f"IATE {entry_id}",
            )
        ],
        confidence=0.85,
        review_status=ReviewStatus.verified,
    )


def lookup_live(
    query: str,
    src_lang: str,
    *,
    langs: tuple[str, ...] = CORE_LANGS,
    limit: int = 10,
    timeout: int = 30,
) -> list[TermRecord]:
    """Live lookup against IATE (EU terminology API).

    Uses exact-term search first; falls back to partial match if nothing is found.
    Intended for request-time use (MCP). Full TBX dumps may be bundled later with
    attribution.
    """
    q = query.strip()
    if not q or src_lang not in SUPPORTED_LANGS:
        return []

    targets = [lang for lang in langs if lang != src_lang and lang in SUPPORTED_LANGS]
    if not targets:
        return []

    base_payload = {
        "query": q,
        "source": src_lang,
        "targets": targets,
        "search_in_fields": [0],
        "search_in_term_types": [4],  # term only (skip abbrev noise)
        "_limit": limit,
    }

    items: list[dict[str, Any]] = []
    for operator in (3, 5):  # exact match, then partial
        payload = {**base_payload, "query_operator": operator}
        items = _post_search(payload, timeout=timeout)
        if items:
            break

    records: list[TermRecord] = []
    seen_ids: set[str] = set()
    for item in items:
        rec = entry_to_term_record(item, langs=langs)
        if rec is None or rec.concept_id in seen_ids:
            continue
        seen_ids.add(rec.concept_id)
        records.append(rec)
        if len(records) >= limit:
            break
    return records
