"""JURIVOC connector — Federal Supreme Court subject-matter thesaurus.

Status: 🟠 ORANGE. License to verify; export format to locate (often SKOS/RDF).
Used to enrich :class:`~openglossa.schemas.TermRecord` with synonyms and
subject-matter domains. P3 stub.
"""

from __future__ import annotations

SOURCE_NAME = "JURIVOC"
LICENSE_TAG = "UNVERIFIED"


def load_concepts(*args, **kwargs):  # noqa: ANN002, ANN003
    """Load JURIVOC SKOS concepts (subjects + synonyms).

    Raises
    ------
    NotImplementedError
        P3 not implemented yet; SKOS/RDF endpoint to be located first
        (see open question in LICENSING.md).
    """
    raise NotImplementedError("JURIVOC ingestion (P3) is not implemented yet.")
