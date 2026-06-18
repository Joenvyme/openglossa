"""Parquet export for the analytic outputs (P5).

Lossless and round-trippable: every record is stored verbatim in a ``record``
column (its canonical JSON), so ``read_parquet`` reconstructs the exact pydantic
instances. A handful of flat index columns (language codes, ids, licence, ...)
are added alongside so the files are directly queryable in DuckDB/polars without
unpacking the JSON.

Requires the optional ``data`` extra: ``pip install 'openglossa[data]'``.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from openglossa.schemas import TermRecord, TranslationUnit


def _import_polars():
    try:
        import polars as pl
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "Parquet export requires the 'data' extra: pip install 'openglossa[data]'"
        ) from exc
    return pl


def _row(rec: BaseModel) -> dict:
    row: dict = {"record": rec.model_dump_json()}
    if isinstance(rec, TranslationUnit):
        row.update(
            tu_id=rec.tu_id,
            src_lang=str(rec.src_lang),
            tgt_lang=str(rec.tgt_lang),
            src=rec.src,
            tgt=rec.tgt,
            source=rec.source.name,
            license=rec.source.license,
            ref=rec.source.ref,
        )
    elif isinstance(rec, TermRecord):
        row.update(
            concept_id=rec.concept_id,
            languages=rec.languages(),
            legal_basis=rec.legal_basis,
            authority=str(rec.authority),
            review_status=str(rec.review_status),
        )
    return row


def write_parquet(records: Iterable[BaseModel], path: str | Path) -> Path:
    """Write records to Parquet (lossless ``record`` column + flat index columns)."""
    pl = _import_polars()
    rows = [_row(r) for r in records]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        df = pl.DataFrame(rows)
    else:
        df = pl.DataFrame(schema={"record": pl.Utf8})
    df.write_parquet(out)
    return out


def read_parquet(model: type[BaseModel], path: str | Path) -> list[BaseModel]:
    """Read a Parquet file back into validated ``model`` instances."""
    pl = _import_polars()
    p = Path(path)
    if not p.exists():
        return []
    df = pl.read_parquet(p, columns=["record"])
    return [model.model_validate_json(s) for s in df["record"].to_list()]
