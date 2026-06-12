"""Report embedding encoder (FSM scouting axis).

Two modes, selected by the PLAYERS_ENCODER env var:

- "e5"   — intfloat/e5-small via sentence-transformers (384-dim), the production
           encoder from FSM v0.2. Requires the optional sentence-transformers install
           and a one-time model download.
- "lite" — deterministic hashing encoder (default). No model download, no heavy deps,
           stable across runs/machines, so dev environments and tests behave identically.
           Quality is below e5 but cosine geometry still reflects shared vocabulary.

Both produce L2-normalized float32 vectors of dimension 384, so stored embeddings are
only comparable within a single mode. Re-run `python -m backend.app.seed` (or
ml/embed_reports.py) after switching modes.
"""

from __future__ import annotations

import hashlib
import math
import os
import re

import numpy as np

DIM = 384

# PDR §2.3: section weighting for the player-level embedding.
SECTION_WEIGHTS = {
    "overview": 0.50,
    "strengths": 0.25,
    "weaknesses": 0.25,
    "sources_tell_us": 0.00,
}

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _lite_encode(text: str) -> np.ndarray:
    """Hashing-trick encoder: unigrams + bigrams -> signed buckets, tf-log weighted."""
    vec = np.zeros(DIM, dtype=np.float64)
    toks = _tokens(text)
    if not toks:
        return vec.astype(np.float32)
    feats: dict[str, int] = {}
    for tok in toks:
        feats[tok] = feats.get(tok, 0) + 1
    for a, b in zip(toks, toks[1:]):
        bg = f"{a} {b}"
        feats[bg] = feats.get(bg, 0) + 1
    for feat, count in feats.items():
        digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        h = int.from_bytes(digest, "big")
        idx = h % DIM
        sign = 1.0 if (h >> 9) & 1 else -1.0
        vec[idx] += sign * (1.0 + math.log(count))
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.astype(np.float32)


class ReportEncoder:
    """Encodes scouting text into 384-dim L2-normalized vectors."""

    def __init__(self, mode: str | None = None):
        self.mode = (mode or os.environ.get("PLAYERS_ENCODER", "lite")).lower()
        self._model = None
        if self.mode == "e5":
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer("intfloat/e5-small")
            except Exception as exc:  # pragma: no cover - depends on optional install
                raise RuntimeError(
                    "PLAYERS_ENCODER=e5 requires `pip install -r requirements-optional.txt`"
                ) from exc

    def _encode(self, text: str, prefix: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(DIM, dtype=np.float32)
        if self._model is not None:
            vec = self._model.encode(f"{prefix}: {text}", normalize_embeddings=True)
            return np.asarray(vec, dtype=np.float32)
        return _lite_encode(text)

    def encode_passage(self, text: str) -> np.ndarray:
        return self._encode(text, "passage")

    def encode_query(self, text: str) -> np.ndarray:
        return self._encode(text, "query")

    def encode_player(
        self,
        overview: str,
        strengths: str,
        weaknesses: str,
        sources_tell_us: str = "",
    ) -> np.ndarray:
        sections = {
            "overview": overview,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "sources_tell_us": sources_tell_us,
        }
        vec = np.zeros(DIM, dtype=np.float64)
        for name, weight in SECTION_WEIGHTS.items():
            if weight <= 0:
                continue
            vec += weight * self._encode(sections[name] or "", "passage").astype(np.float64)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.astype(np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity for already-normalized (or zero) vectors, clamped to [0, 1]."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    sim = float(np.dot(a, b) / (na * nb))
    return max(0.0, min(1.0, sim))
