from __future__ import annotations

from xml.etree import ElementTree as ET

from openglossa.export import (
    TBX_DTD,
    TMX_DTD,
    read_jsonl,
    read_parquet,
    validate_tbx,
    validate_tmx,
    validate_with_dtd,
    write_jsonl,
    write_parquet,
    write_tbx,
    write_tmx,
)
from openglossa.export.deepl_csv import deepl_pairs, write_deepl_glossary
from openglossa.schemas import TermRecord, TranslationUnit

# --------------------------------------------------------------------------- #
# Round-trip: export -> re-import -> equality (PROJECT.md P5 acceptance)
# --------------------------------------------------------------------------- #


def test_jsonl_roundtrip_tus(translation_units, tmp_path):
    path = write_jsonl(translation_units, tmp_path / "tus.jsonl")
    assert read_jsonl(TranslationUnit, path) == translation_units


def test_jsonl_roundtrip_terms(term_records, tmp_path):
    path = write_jsonl(term_records, tmp_path / "terms.jsonl")
    assert read_jsonl(TermRecord, path) == term_records


def test_parquet_roundtrip_tus(translation_units, tmp_path):
    path = write_parquet(translation_units, tmp_path / "tus.parquet")
    assert read_parquet(TranslationUnit, path) == translation_units


def test_parquet_roundtrip_terms(term_records, tmp_path):
    path = write_parquet(term_records, tmp_path / "terms.parquet")
    assert read_parquet(TermRecord, path) == term_records


def test_parquet_has_flat_index_columns(translation_units, tmp_path):
    import polars as pl

    path = write_parquet(translation_units, tmp_path / "tus.parquet")
    df = pl.read_parquet(path)
    assert {"record", "tu_id", "src_lang", "tgt_lang", "src", "tgt"} <= set(df.columns)


def test_deepl_csv_roundtrip(term_records, tmp_path):
    path = write_deepl_glossary(term_records, "de", "fr", tmp_path / "de-fr.csv")
    reimported = [
        tuple(line.split(",", 1))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert reimported == deepl_pairs(term_records, "de", "fr")


# --------------------------------------------------------------------------- #
# Validation: structural + DTD
# --------------------------------------------------------------------------- #


def test_tmx_validates_structural_and_dtd(translation_units, tmp_path):
    path = write_tmx(translation_units, tmp_path / "tm.tmx")
    assert validate_tmx(path) == []
    assert validate_with_dtd(path, TMX_DTD) == []


def test_tbx_validates_structural_and_dtd(term_records, tmp_path):
    path = write_tbx(term_records, tmp_path / "tb.tbx")
    assert validate_tbx(path) == []
    assert validate_with_dtd(path, TBX_DTD) == []


def test_validate_tmx_detects_problems():
    # A <tu> with a single <tuv> and a <tuv> missing xml:lang / seg.
    tmx = ET.fromstring(
        '<tmx version="1.4"><header creationtool="x" segtype="sentence" '
        'srclang="de" adminlang="en" datatype="plaintext" o-tmf="x"/>'
        "<body><tu><tuv><seg></seg></tuv></tu></body></tmx>"
    )
    problems = validate_tmx(tmx)
    assert any("expected >= 2" in p for p in problems)
    assert any("xml:lang" in p for p in problems)


def test_validate_tbx_detects_problems():
    tbx = ET.fromstring(
        '<tbx type="TBX-Basic"><tbxHeader><fileDesc><titleStmt><title>t</title>'
        "</titleStmt></fileDesc></tbxHeader><text><body>"
        '<conceptEntry id="og:term:x"><langSec/></conceptEntry>'
        "</body></text></tbx>"
    )
    problems = validate_tbx(tbx)
    assert any("xml:lang" in p for p in problems)
    assert any("without any <term>" in p for p in problems)
