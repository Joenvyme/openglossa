"""Guard tests keeping code in sync with the license registry (hard rule #6)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_licensing_file_lists_orange_sources():
    text = (ROOT / "LICENSING.md").read_text(encoding="utf-8")
    for src in ("TERMDAT", "JURIVOC", "OpenCaseLaw"):
        assert src in text


def test_termdat_redistribution_not_confirmed_by_default():
    from openglossa.sources import termdat

    assert termdat.REDISTRIBUTION_CONFIRMED is False
    import pytest

    with pytest.raises(PermissionError):
        termdat.assert_redistribution_allowed()
