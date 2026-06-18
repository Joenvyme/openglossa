"""Validation for the XML exports (P5).

Two layers:

* **Structural** validators (`validate_tmx`, `validate_tbx`) — stdlib only, always
  available. They check the document is well-formed and carries the required
  TMX/TBX structure and provenance. Return a list of problems (empty = valid).
* **DTD** validation (`validate_with_dtd`) — uses ``lxml`` against the bundled
  ``schemas/dtd/tmx14.dtd`` (canonical LISA OSCAR DTD) and
  ``schemas/dtd/tbx_openglossa.dtd`` (the TBX-Basic DCA subset we emit).

The bundled DTD paths are exposed as :data:`TMX_DTD` and :data:`TBX_DTD`.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

_DTD_DIR = Path(__file__).resolve().parents[3] / "schemas" / "dtd"
TMX_DTD = _DTD_DIR / "tmx14.dtd"
TBX_DTD = _DTD_DIR / "tbx_openglossa.dtd"


def _root(source: str | Path | ET.ElementTree | ET.Element) -> ET.Element:
    if isinstance(source, ET.Element):
        return source
    if isinstance(source, ET.ElementTree):
        return source.getroot()
    return ET.parse(str(source)).getroot()


def validate_tmx(source: str | Path | ET.ElementTree | ET.Element) -> list[str]:
    """Structurally validate a TMX 1.4 document. Returns a list of problems."""
    problems: list[str] = []
    root = _root(source)
    if root.tag != "tmx":
        return [f"root element is <{root.tag}>, expected <tmx>"]
    if root.get("version") != "1.4":
        problems.append(f"tmx version is {root.get('version')!r}, expected '1.4'")

    header = root.find("header")
    if header is None:
        problems.append("missing <header>")
    else:
        for attr in ("creationtool", "segtype", "srclang", "adminlang", "datatype", "o-tmf"):
            if not header.get(attr):
                problems.append(f"<header> missing required attribute '{attr}'")

    body = root.find("body")
    if body is None:
        problems.append("missing <body>")
        return problems

    for i, tu in enumerate(body.findall("tu")):
        tuvs = tu.findall("tuv")
        if len(tuvs) < 2:
            problems.append(f"tu[{i}] has {len(tuvs)} <tuv>, expected >= 2")
        for tuv in tuvs:
            if not tuv.get(_XML_LANG):
                problems.append(f"tu[{i}] has a <tuv> without xml:lang")
            seg = tuv.find("seg")
            if seg is None or not (seg.text and seg.text.strip()):
                problems.append(f"tu[{i}] has a <tuv> without a non-empty <seg>")
    return problems


def validate_tbx(source: str | Path | ET.ElementTree | ET.Element) -> list[str]:
    """Structurally validate a TBX (DCA) document. Returns a list of problems."""
    problems: list[str] = []
    root = _root(source)
    if root.tag != "tbx":
        return [f"root element is <{root.tag}>, expected <tbx>"]

    if root.find("tbxHeader/fileDesc/titleStmt/title") is None:
        problems.append("missing <tbxHeader>/<fileDesc>/<titleStmt>/<title>")
    body = root.find("text/body")
    if body is None:
        problems.append("missing <text>/<body>")
        return problems

    for i, entry in enumerate(body.findall("conceptEntry")):
        if not entry.get("id"):
            problems.append(f"conceptEntry[{i}] missing 'id'")
        lang_secs = entry.findall("langSec")
        if not lang_secs:
            problems.append(f"conceptEntry[{i}] has no <langSec>")
        for ls in lang_secs:
            if not ls.get(_XML_LANG):
                problems.append(f"conceptEntry[{i}] has a <langSec> without xml:lang")
            terms = ls.findall("termSec/term")
            if not terms:
                problems.append(f"conceptEntry[{i}] has a <langSec> without any <term>")
            for t in terms:
                if not (t.text and t.text.strip()):
                    problems.append(f"conceptEntry[{i}] has an empty <term>")
    return problems


def validate_with_dtd(xml_path: str | Path, dtd_path: str | Path) -> list[str]:
    """Validate an XML file against a DTD using lxml. Returns a list of problems.

    Raises ImportError if lxml (the ``sources`` extra) is unavailable.
    """
    try:
        from lxml import etree
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "DTD validation requires lxml: pip install 'openglossa[sources]'"
        ) from exc

    dtd = etree.DTD(str(dtd_path))
    doc = etree.parse(str(xml_path))
    if dtd.validate(doc):
        return []
    return [str(err) for err in dtd.error_log]
