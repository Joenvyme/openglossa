from __future__ import annotations

from xml.etree import ElementTree as ET

from openglossa.export import write_deepl_glossary, write_tbx, write_tmx


def test_deepl_glossary(term_records, tmp_path):
    out = write_deepl_glossary(term_records, "de", "fr", tmp_path / "de-fr.csv")
    content = out.read_text(encoding="utf-8").strip()
    assert content == "Verzug,demeure"


def test_tmx_is_valid_xml_with_provenance(translation_units, tmp_path):
    out = write_tmx(translation_units, tmp_path / "tm.tmx")
    root = ET.parse(out).getroot()
    assert root.tag == "tmx"
    tus = root.findall(".//tu")
    assert len(tus) == 1
    props = {p.get("type"): p.text for p in tus[0].findall("prop")}
    assert props["x-source"] == "SLDS"
    assert props["x-license"] == "CC-BY-4.0"
    segs = [s.text for s in tus[0].findall(".//seg")]
    assert "Le débiteur est en demeure." in segs


def test_tbx_is_valid_xml(term_records, tmp_path):
    out = write_tbx(term_records, tmp_path / "tb.tbx")
    root = ET.parse(out).getroot()
    assert root.tag == "tbx"
    entries = root.findall(".//conceptEntry")
    assert len(entries) == 1
    terms = [t.text for t in entries[0].findall(".//term")]
    assert {"Verzug", "demeure", "mora"} <= set(terms)
