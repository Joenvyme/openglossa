"""Export formats (P5): TBX, TMX, DeepL glossary CSV, Parquet.

All exporters must respect hard rule #6: never serialize raw upstream text from a
source whose redistribution is not confirmed (see LICENSING.md / termdat).
"""

from __future__ import annotations

from openglossa.export.deepl_csv import write_deepl_glossary
from openglossa.export.tbx import write_tbx
from openglossa.export.tmx import write_tmx

__all__ = ["write_tbx", "write_tmx", "write_deepl_glossary", "write_parquet"]


def write_parquet(*args, **kwargs):  # noqa: ANN002, ANN003
    """Write records to Parquet (via polars). P5 stub."""
    raise NotImplementedError("Parquet export (P5) is not implemented yet.")
