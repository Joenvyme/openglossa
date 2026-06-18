"""TMX 1.4 export for the translation memory.

Generates valid TMX using the stdlib XML writer (no optional deps). Each
:class:`~openglossa.schemas.TranslationUnit` becomes one ``<tu>`` with two
``<tuv>`` segments and provenance carried in ``<prop>`` elements (source name,
URI, license, reference) — honouring hard rule #3.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from openglossa.schemas import TranslationUnit

CREATION_TOOL = "OpenGlossa"
CREATION_TOOL_VERSION = "0.1.0"


def _as_str(value) -> str:
    return str(value) if value is not None else ""


def build_tmx(units: Iterable[TranslationUnit]) -> ET.ElementTree:
    units = list(units)
    src_lang = _as_str(units[0].src_lang) if units else "de"

    tmx = ET.Element("tmx", version="1.4")
    header = ET.SubElement(
        tmx,
        "header",
        {
            "creationtool": CREATION_TOOL,
            "creationtoolversion": CREATION_TOOL_VERSION,
            "segtype": "sentence",
            "o-tmf": "OpenGlossa-JSONL",
            "adminlang": "en",
            "srclang": src_lang,
            "datatype": "plaintext",
            "creationdate": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        },
    )
    header.text = ""
    body = ET.SubElement(tmx, "body")

    for unit in units:
        tu = ET.SubElement(body, "tu", {"tuid": unit.tu_id})
        for prop_type, value in (
            ("x-source", unit.source.name),
            ("x-source-uri", _as_str(unit.source.uri)),
            ("x-license", unit.source.license),
            ("x-reference", unit.source.ref or ""),
            ("x-domain", ",".join(unit.domain)),
        ):
            if value:
                prop = ET.SubElement(tu, "prop", {"type": prop_type})
                prop.text = value

        for lang, text in ((_as_str(unit.src_lang), unit.src), (_as_str(unit.tgt_lang), unit.tgt)):
            tuv = ET.SubElement(tu, "tuv", {"{http://www.w3.org/XML/1998/namespace}lang": lang})
            seg = ET.SubElement(tuv, "seg")
            seg.text = text

    return ET.ElementTree(tmx)


def write_tmx(units: Iterable[TranslationUnit], path: str | Path) -> Path:
    """Write a TMX 1.4 file. Returns the written path."""
    tree = build_tmx(units)
    ET.indent(tree, space="  ")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out
