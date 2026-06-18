"""Akoma Ntoso (LegalDocML) parsing for Fedlex consolidated XML.

Fedlex serves consolidated acts as Akoma Ntoso 3.0 XML. Articles carry an
``eId`` (e.g. ``art_1``) and paragraphs a nested ``eId`` (``art_1/para_1``).
The ``eId`` is **stable across languages**, which is exactly the structural key
OpenGlossa aligns on (method ``eli-structural``).

This module turns such XML into an ordered ``eId -> text`` mapping at paragraph
(alinéa) granularity, falling back to article granularity for articles without
paragraphs. It is a pure function (no network), so it is unit-tested offline.

The ``lxml`` dependency is optional (``pip install 'openglossa[sources]'``).
"""

from __future__ import annotations

import re

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
_Q = "{" + AKN_NS + "}"

_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", text).strip()


def _text_of(element) -> str:
    """Concatenate visible text under an element (e.g. an akn:content)."""
    return _normalize("".join(element.itertext()))


def parse_segments(xml: str | bytes) -> dict[str, str]:
    """Parse Akoma Ntoso XML into an ordered ``eId -> text`` mapping.

    Segments are emitted at paragraph (alinéa) level when an article has
    paragraphs, otherwise at article level. Empty segments are skipped.

    Raises
    ------
    ImportError
        If the optional ``sources`` extra (lxml) is not installed.
    """
    try:
        from lxml import etree
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "parse_segments requires the 'sources' extra: pip install 'openglossa[sources]'"
        ) from exc

    data = xml.encode("utf-8") if isinstance(xml, str) else xml
    # recover=True tolerates the stray migration namespaces Fedlex emits on <p>.
    root = etree.fromstring(data, parser=etree.XMLParser(recover=True, huge_tree=True))

    # Drop non-normative editorial apparatus (amendment footnotes carry AS/BBl
    # citations and "In Kraft seit ..." notes that pollute both the TM and term
    # mining). They are not part of the statutory text.
    for note in root.findall(f".//{_Q}authorialNote"):
        parent = note.getparent()
        if parent is None:
            continue
        # Preserve the text that follows the footnote marker (its tail).
        tail = note.tail or ""
        prev = note.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
        parent.remove(note)

    segments: dict[str, str] = {}
    for article in root.iter(f"{_Q}article"):
        art_eid = article.get("eId")
        if not art_eid:
            continue
        paragraphs = article.findall(f".//{_Q}paragraph")
        emitted = False
        for para in paragraphs:
            para_eid = para.get("eId")
            content = para.find(f".//{_Q}content")
            if not para_eid or content is None:
                continue
            text = _text_of(content)
            if text:
                segments[para_eid] = text
                emitted = True
        if not emitted:
            content = article.find(f".//{_Q}content")
            if content is not None:
                text = _text_of(content)
                if text:
                    segments[art_eid] = text
    return segments


def ref_from_eid(rs_number: str, eid: str) -> str:
    """Build a human citation from an eId, e.g. ('220', 'art_6_a/para_2') ->
    'SR 220 Art. 6a al. 2'."""
    parts = eid.split("/")
    art = parts[0].removeprefix("art_").replace("_", "")
    ref = f"SR {rs_number} Art. {art}"
    if len(parts) > 1 and parts[1].startswith("para_"):
        ref += f" al. {parts[1].removeprefix('para_')}"
    return ref


_ART_RE = re.compile(r"\bart\.?\s*([0-9]+)\s*([a-z]?)\b", re.IGNORECASE)
# alinéa / Absatz / capoverso / paragraph, all map to the AKN para_ component.
_PARA_RE = re.compile(r"\b(?:al|abs|cpv|para)\.?\s*([0-9]+)\b", re.IGNORECASE)


def eid_from_citation(citation: str) -> str | None:
    """Inverse of :func:`ref_from_eid`: map a human citation to an eId.

    ``'SR 220 Art. 6a al. 2'`` -> ``'art_6_a/para_2'``. Returns ``None`` when no
    article can be parsed (the RS number, if present, is ignored here).
    """
    art = _ART_RE.search(citation)
    if not art:
        return None
    eid = f"art_{art.group(1)}"
    if art.group(2):
        eid += f"_{art.group(2).lower()}"
    para = _PARA_RE.search(citation)
    if para:
        eid += f"/para_{para.group(1)}"
    return eid
