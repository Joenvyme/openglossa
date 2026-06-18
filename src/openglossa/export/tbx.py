"""TBX (TermBase eXchange) export for the termbase.

Produces a TBX-Basic-flavoured document with the stdlib XML writer. Each
:class:`~openglossa.schemas.TermRecord` becomes a ``<termEntry>`` (here a
``conceptEntry``) with one ``<langSec>`` per language and provenance carried as
notes/admin info (hard rule #3).

This is a pragmatic generator suitable for the PoC; strict DTD/XSD validation is
wired in P5.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from xml.etree import ElementTree as ET

from openglossa.schemas import TermRecord


def _as_str(value) -> str:
    return str(value) if value is not None else ""


def build_tbx(records: Iterable[TermRecord]) -> ET.ElementTree:
    tbx = ET.Element("tbx", {"type": "TBX-Basic", "style": "dca"})
    tbx_header = ET.SubElement(tbx, "tbxHeader")
    file_desc = ET.SubElement(tbx_header, "fileDesc")
    title_stmt = ET.SubElement(file_desc, "titleStmt")
    ET.SubElement(title_stmt, "title").text = "OpenGlossa termbase"
    source_desc = ET.SubElement(file_desc, "sourceDesc")
    ET.SubElement(source_desc, "p").text = (
        "Derived from official Swiss legal sources. Not the authoritative legal text."
    )

    text_el = ET.SubElement(tbx, "text")
    body = ET.SubElement(text_el, "body")

    for rec in records:
        entry = ET.SubElement(body, "conceptEntry", {"id": rec.concept_id})

        if rec.domain:
            descrip = ET.SubElement(entry, "descrip", {"type": "subjectField"})
            descrip.text = ", ".join(rec.domain)
        for basis in rec.legal_basis:
            ET.SubElement(entry, "descrip", {"type": "legalBasis"}).text = basis
        for src in rec.sources:
            ET.SubElement(entry, "admin", {"type": "source"}).text = (
                f"{src.name}: {_as_str(src.uri)} ({src.license})"
            )

        for lang, terms in rec.terms.items():
            if not terms:
                continue
            lang_str = _as_str(lang)
            lang_sec = ET.SubElement(
                entry,
                "langSec",
                {"{http://www.w3.org/XML/1998/namespace}lang": lang_str},
            )
            definition = rec.definition.get(lang)
            if definition:
                ET.SubElement(lang_sec, "descrip", {"type": "definition"}).text = definition
            for term in terms:
                term_sec = ET.SubElement(lang_sec, "termSec")
                ET.SubElement(term_sec, "term").text = term.text
                if term.pos:
                    ET.SubElement(
                        term_sec, "termNote", {"type": "partOfSpeech"}
                    ).text = _as_str(term.pos)
                ET.SubElement(
                    term_sec, "termNote", {"type": "administrativeStatus"}
                ).text = _as_str(term.status)

    return ET.ElementTree(tbx)


def write_tbx(records: Iterable[TermRecord], path: str | Path) -> Path:
    """Write a TBX file. Returns the written path."""
    tree = build_tbx(records)
    ET.indent(tree, space="  ")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out
