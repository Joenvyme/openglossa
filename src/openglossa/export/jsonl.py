"""JSONL export/import for records (stdlib only).

One pydantic model per line. Used as the canonical interchange format between
pipeline phases (PROJECT.md §6).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel


def write_jsonl(records: Iterable[BaseModel], path: str | Path) -> Path:
    """Write pydantic models as JSONL. Returns the written path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(rec.model_dump_json())
            fh.write("\n")
    return out


def read_jsonl(model: type[BaseModel], path: str | Path) -> list[BaseModel]:
    """Read JSONL into validated instances of ``model``."""
    p = Path(path)
    if not p.exists():
        return []
    return [
        model.model_validate_json(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
