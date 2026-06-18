"""Export formats (P5): TBX, TMX, DeepL glossary CSV, JSONL, Parquet.

All exporters must respect hard rule #6: never serialize raw upstream text from a
source whose redistribution is not confirmed (see LICENSING.md / termdat).
"""

from __future__ import annotations

from openglossa.export.deepl_csv import write_deepl_glossary
from openglossa.export.jsonl import read_jsonl, write_jsonl
from openglossa.export.parquet import read_parquet, write_parquet
from openglossa.export.tbx import write_tbx
from openglossa.export.tmx import write_tmx
from openglossa.export.validate import (
    TBX_DTD,
    TMX_DTD,
    validate_tbx,
    validate_tmx,
    validate_with_dtd,
)

__all__ = [
    "write_tbx",
    "write_tmx",
    "write_deepl_glossary",
    "write_jsonl",
    "read_jsonl",
    "write_parquet",
    "read_parquet",
    "validate_tbx",
    "validate_tmx",
    "validate_with_dtd",
    "TBX_DTD",
    "TMX_DTD",
]
