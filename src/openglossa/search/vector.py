"""Vector index over the translation memory using sqlite-vec.

Each TranslationUnit is indexed as **two rows** (one per side/language) so that a
query in ``src_lang`` is matched against same-language segments and returns the
aligned counterpart in ``tgt_lang`` — direction-agnostic, like the lexical
baseline, but semantic.

Encoders are pluggable:

* :class:`HashingEncoder` — deterministic, dependency-free (token-hashing bag of
  words). Not semantic, but lets the index mechanics be tested offline/CI.
* :func:`load_labse` — the production multilingual encoder (LaBSE) via
  sentence-transformers (``ml`` extra; downloads the model on first use).

Requires sqlite-vec (``data`` extra): ``pip install 'openglossa[data]'``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import struct
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from openglossa.schemas import TranslationUnit

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


@runtime_checkable
class Encoder(Protocol):
    """Encodes texts into L2-normalised float vectors of fixed dimension."""

    name: str
    dim: int

    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashingEncoder:
    """Deterministic token-hashing encoder (no model download).

    Cosine similarity in this space approximates lexical overlap, which is enough
    to exercise the vector-index pipeline deterministically in tests.
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim
        self.name = f"hashing-{dim}"

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for tok in _WORD.findall(text.casefold()):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            out.append([x / norm for x in vec])
        return out


class _SentenceTransformerEncoder:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - exercised only without extra
            raise ImportError(
                "LaBSE requires the 'ml' extra: pip install 'openglossa[ml]'"
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.name = model_name
        # sentence-transformers renamed this method; support both.
        if hasattr(self._model, "get_embedding_dimension"):
            self.dim = int(self._model.get_embedding_dimension())
        else:
            self.dim = int(self._model.get_sentence_embedding_dimension())

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vecs = self._model.encode(
            list(texts), normalize_embeddings=True, convert_to_numpy=True
        )
        return [v.tolist() for v in vecs]


def load_labse(model_name: str = "sentence-transformers/LaBSE") -> Encoder:
    """Load the production multilingual encoder (LaBSE)."""
    return _SentenceTransformerEncoder(model_name)


# A lighter multilingual encoder (~470 MB, 384-dim) that fits a 2 GB host while
# staying well above the lexical baseline. Good DE/FR/IT coverage.
MINILM_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_minilm(model_name: str = MINILM_MODEL) -> Encoder:
    """Load the light multilingual encoder (paraphrase-multilingual MiniLM)."""
    return _SentenceTransformerEncoder(model_name)


def encoder_for_name(name: str) -> Encoder:
    """Reconstruct the encoder used to build an index, from its stored name.

    Lets the server open any index without knowing its encoder in advance:
    hashing encoders are rebuilt from their dimension, model-backed encoders
    (a name containing ``/``) from their sentence-transformers model id.
    """
    if name.startswith("hashing-"):
        return HashingEncoder(int(name.split("-", 1)[1]))
    return _SentenceTransformerEncoder(name)


def _serialize(vec: Sequence[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _sqlite_module():
    """Return a sqlite3-compatible module that supports loadable extensions.

    Some CPython builds (e.g. Render's) are compiled without
    ``--enable-loadable-sqlite-extensions``, so ``enable_load_extension`` is
    missing. ``pysqlite3`` (the ``pysqlite3-binary`` wheel) bundles a SQLite that
    allows it; prefer it when present, otherwise fall back to stdlib ``sqlite3``.
    """
    try:
        import pysqlite3  # type: ignore[import-not-found]

        return pysqlite3
    except ImportError:
        return sqlite3


def _connect(path: str | Path) -> sqlite3.Connection:
    try:
        import sqlite_vec
    except ImportError as exc:  # pragma: no cover - exercised only without extra
        raise ImportError(
            "Vector index requires sqlite-vec (the 'data' extra): "
            "pip install 'openglossa[data]'"
        ) from exc
    db = _sqlite_module().connect(str(path))
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


class VectorIndex:
    """A sqlite-vec backed semantic index over translation units."""

    def __init__(self, db: sqlite3.Connection, encoder: Encoder) -> None:
        self.db = db
        self.encoder = encoder

    # -- construction ------------------------------------------------------- #

    @classmethod
    def build(
        cls,
        tus: Sequence[TranslationUnit],
        encoder: Encoder,
        path: str | Path,
        *,
        batch_size: int = 1000,
    ) -> VectorIndex:
        """Build (overwrite) a vector index file from ``tus``.

        Texts are encoded and inserted in batches of ``batch_size`` rows so peak
        memory stays bounded on large corpora and small hosts.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            p.unlink()
        db = _connect(p)
        db.execute(
            f"CREATE VIRTUAL TABLE vec_items USING vec0("
            f"embedding float[{encoder.dim}] distance_metric=cosine)"
        )
        db.execute(
            "CREATE TABLE meta ("
            "rowid INTEGER PRIMARY KEY, lang TEXT, text TEXT, "
            "pair_lang TEXT, pair_text TEXT, source TEXT)"
        )
        db.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
        db.execute(
            "INSERT INTO config VALUES ('encoder', ?), ('dim', ?)",
            (encoder.name, str(encoder.dim)),
        )

        rows: list[tuple[str, str, str, str, str]] = []
        for tu in tus:
            src_meta = json.dumps(
                {"name": tu.source.name, "ref": tu.source.ref, "uri": str(tu.source.uri)}
            )
            rows.append((str(tu.src_lang), tu.src, str(tu.tgt_lang), tu.tgt, src_meta))
            rows.append((str(tu.tgt_lang), tu.tgt, str(tu.src_lang), tu.src, src_meta))

        # Encode and insert in batches so peak memory stays bounded (large
        # corpora would otherwise hold hundreds of MB of vectors at once).
        rowid = 0
        for start in range(0, len(rows), batch_size):
            chunk = rows[start : start + batch_size]
            embeddings = encoder.encode([r[1] for r in chunk])
            for row, emb in zip(chunk, embeddings, strict=True):
                rowid += 1
                db.execute(
                    "INSERT INTO vec_items(rowid, embedding) VALUES (?, ?)",
                    (rowid, _serialize(emb)),
                )
                db.execute("INSERT INTO meta VALUES (?, ?, ?, ?, ?, ?)", (rowid, *row))
            db.commit()
        return cls(db, encoder)

    @classmethod
    def open(cls, path: str | Path, encoder: Encoder) -> VectorIndex:
        """Open an existing index; validates the encoder matches the build."""
        db = _connect(path)
        cfg = dict(db.execute("SELECT key, value FROM config").fetchall())
        if cfg.get("encoder") != encoder.name:
            raise ValueError(
                f"index built with encoder {cfg.get('encoder')!r}, "
                f"got {encoder.name!r}"
            )
        return cls(db, encoder)

    @classmethod
    def open_auto(cls, path: str | Path) -> VectorIndex:
        """Open an existing index, reconstructing its encoder from the stored name.

        The index is self-describing, so the caller need not know which encoder
        (LaBSE, MiniLM, hashing, …) was used to build it.
        """
        db = _connect(path)
        cfg = dict(db.execute("SELECT key, value FROM config").fetchall())
        encoder = encoder_for_name(cfg.get("encoder", ""))
        return cls(db, encoder)

    # -- query -------------------------------------------------------------- #

    def search(
        self, text: str, src_lang: str, tgt_lang: str, k: int = 5
    ) -> list[dict]:
        """Return up to ``k`` nearest parallel examples for the direction."""
        qv = _serialize(self.encoder.encode([text])[0])
        overfetch = max(k * 10, 50)
        candidates = self.db.execute(
            "SELECT rowid, distance FROM vec_items "
            "WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
            (qv, overfetch),
        ).fetchall()

        hits: list[dict] = []
        for rowid, distance in candidates:
            lang, src_text, pair_lang, pair_text, source = self.db.execute(
                "SELECT lang, text, pair_lang, pair_text, source FROM meta WHERE rowid = ?",
                (rowid,),
            ).fetchone()
            if lang != src_lang or pair_lang != tgt_lang:
                continue
            hits.append(
                {
                    "src": src_text,
                    "tgt": pair_text,
                    "source": json.loads(source),
                    "score": round(max(0.0, 1.0 - float(distance)), 4),
                }
            )
            if len(hits) >= k:
                break
        return hits

    def close(self) -> None:
        self.db.close()
