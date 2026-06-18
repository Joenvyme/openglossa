"""Pydantic v2 data models for OpenGlossa.

Two record types form the dataset:

* :class:`TermRecord` — concept-centred entry (equivalent of a TBX ``termEntry``).
* :class:`TranslationUnit` — a parallel segment (a TM unit).

Hard rule #3 (provenance per record) is enforced structurally: every record
carries at least one :class:`SourceRef` with a URI and a license. Hard rule #4
(no fabrication) is reflected by the ``review_status`` / ``supported`` semantics
used downstream.

Run ``python -m openglossa.schemas`` to dump the JSON Schemas into ``schemas/``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

# --------------------------------------------------------------------------- #
# Controlled vocabularies
# --------------------------------------------------------------------------- #


class Lang(StrEnum):
    """Supported language codes (ISO 639-1)."""

    de = "de"
    fr = "fr"
    it = "it"
    rm = "rm"
    en = "en"


class PartOfSpeech(StrEnum):
    noun = "noun"
    verb = "verb"
    adjective = "adjective"
    adverb = "adverb"
    phrase = "phrase"
    abbreviation = "abbreviation"
    other = "other"


class TermStatus(StrEnum):
    preferred = "preferred"
    admitted = "admitted"
    deprecated = "deprecated"


class Authority(StrEnum):
    statutory = "statutory"
    jurisprudential = "jurisprudential"
    administrative = "administrative"


class ReviewStatus(StrEnum):
    candidate = "candidate"
    verified = "verified"
    rejected = "rejected"


class AlignmentMethod(StrEnum):
    eli_structural = "eli-structural"
    labse = "labse"
    manual = "manual"


# --------------------------------------------------------------------------- #
# Shared building blocks
# --------------------------------------------------------------------------- #


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SourceRef(BaseModel):
    """Provenance for a record (hard rule #3).

    A record without provenance must never be ingested, so ``uri`` and
    ``license`` are required.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Upstream source name, e.g. 'Fedlex', 'SLDS', 'TERMDAT'.")
    uri: HttpUrl = Field(..., description="Citable URI of the upstream record.")
    license: str = Field(..., description="SPDX id or short tag, e.g. 'CC-BY-4.0', 'OGD-open-use'.")
    ref: str | None = Field(
        default=None,
        description="Human citation, e.g. 'SR 220 Art. 102' or 'BGE 146 IV 226'.",
    )
    retrieved_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp of retrieval.",
    )


class Term(BaseModel):
    """A single surface form in one language."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    pos: PartOfSpeech | None = None
    status: TermStatus = TermStatus.admitted

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("term text must not be blank")
        return v


Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


# --------------------------------------------------------------------------- #
# Term record (concept-centred)
# --------------------------------------------------------------------------- #


class TermRecord(BaseModel):
    """Concept-centred terminology entry (≈ TBX ``termEntry``)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    concept_id: str = Field(..., pattern=r"^og:term:[A-Za-z0-9_-]+$")
    domain: list[str] = Field(default_factory=list)
    legal_basis: list[str] = Field(
        default_factory=list,
        description="Statutory anchors, e.g. ['SR 220 Art. 102'].",
    )
    definition: dict[Lang, str] = Field(default_factory=dict)
    terms: dict[Lang, list[Term]] = Field(default_factory=dict)
    authority: Authority
    sources: list[SourceRef] = Field(..., min_length=1)
    confidence: Confidence = 1.0
    review_status: ReviewStatus = ReviewStatus.candidate

    @model_validator(mode="after")
    def _at_least_one_term(self) -> TermRecord:
        if not any(self.terms.get(lang) for lang in self.terms):
            raise ValueError("a TermRecord must contain at least one term in one language")
        return self

    def languages(self) -> list[str]:
        """Languages that actually carry at least one term."""
        return [lang for lang, terms in self.terms.items() if terms]

    def preferred(self, lang: Lang | str) -> str | None:
        """Return the preferred (or first) surface form for ``lang``."""
        key = lang.value if isinstance(lang, Lang) else lang
        terms = self.terms.get(key) or self.terms.get(Lang(key))  # tolerate enum/str keys
        if not terms:
            return None
        for t in terms:
            status = t.status.value if isinstance(t.status, TermStatus) else t.status
            if status == TermStatus.preferred.value:
                return t.text
        return terms[0].text


# --------------------------------------------------------------------------- #
# Translation unit (parallel segment)
# --------------------------------------------------------------------------- #


class Alignment(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    method: AlignmentMethod
    score: Confidence = 1.0


class TranslationUnit(BaseModel):
    """A parallel segment pair (a TM unit)."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    tu_id: str = Field(..., pattern=r"^og:tu:[A-Za-z0-9_-]+$")
    src_lang: Lang
    tgt_lang: Lang
    src: str = Field(..., min_length=1)
    tgt: str = Field(..., min_length=1)
    domain: list[str] = Field(default_factory=list)
    source: SourceRef
    alignment: Alignment

    @model_validator(mode="after")
    def _distinct_langs(self) -> TranslationUnit:
        if self.src_lang == self.tgt_lang:
            raise ValueError("src_lang and tgt_lang must differ")
        return self


# --------------------------------------------------------------------------- #
# JSON Schema export
# --------------------------------------------------------------------------- #

SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "term_record": TermRecord,
    "translation_unit": TranslationUnit,
}


def export_json_schemas(out_dir: str | Path = "schemas") -> list[Path]:
    """Write one ``<name>.schema.json`` per model. Returns written paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in SCHEMA_MODELS.items():
        path = out / f"{name}.schema.json"
        path.write_text(
            json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def main() -> None:
    paths = export_json_schemas()
    for p in paths:
        print(f"wrote {p}")


if __name__ == "__main__":
    main()
