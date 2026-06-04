from __future__ import annotations

from typing import List, Optional, Tuple, Union

import numpy as np

# ── Threshold constants (ArcFace 512-dim space) ───────────────────────────
# ArcFace cosine similarity between same-person embeddings is typically > 0.40
# Cross-person similarity is typically < 0.25 at most
COSINE_THRESHOLD_CONFIDENT = 0.45   # very confident match
COSINE_THRESHOLD_MATCH     = 0.35   # acceptable match (used in production)
COSINE_THRESHOLD_UNCERTAIN = 0.28   # uncertain — ask for re-scan

# Legacy alias — used by attendance_pipeline.py
COSINE_THRESHOLD = COSINE_THRESHOLD_MATCH


def cosine_similarity(
    a: Union[List[float], np.ndarray],
    b: Union[List[float], np.ndarray],
) -> float:
    """
    Cosine similarity between two embedding vectors.
    Returns float in [-1, 1]; 1 = identical direction, 0 = orthogonal.
    Both vectors should be L2-normalised (as produced by face_encoder.py).
    """
    a_arr = np.asarray(a, dtype=np.float64)
    b_arr = np.asarray(b, dtype=np.float64)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def euclidean_distance(
    a: Union[List[float], np.ndarray],
    b: Union[List[float], np.ndarray],
) -> float:
    """Euclidean distance between two embedding vectors (smaller = more similar)."""
    a_arr = np.asarray(a, dtype=np.float64)
    b_arr = np.asarray(b, dtype=np.float64)
    return float(np.linalg.norm(a_arr - b_arr))


def confidence_label(cosine_sim: float) -> str:
    """Human-readable confidence tier from a cosine similarity score."""
    if cosine_sim >= COSINE_THRESHOLD_CONFIDENT:
        return "high"
    elif cosine_sim >= COSINE_THRESHOLD_MATCH:
        return "medium"
    elif cosine_sim >= COSINE_THRESHOLD_UNCERTAIN:
        return "low"
    else:
        return "no_match"


def batch_match_best(
    probe: Union[List[float], np.ndarray],
    gallery: np.ndarray,
) -> Tuple[int, float]:
    """
    Efficiently find the best matching embedding in a gallery using
    vectorised numpy dot products (much faster than a Python loop for
    galleries with many students).

    Args:
        probe  : 1-D array, shape (D,)  — query embedding
        gallery: 2-D array, shape (N, D) — stored embeddings matrix

    Returns:
        (best_index, cosine_similarity_score)
    """
    probe_arr   = np.asarray(probe,   dtype=np.float64)
    gallery_arr = np.asarray(gallery, dtype=np.float64)

    # Normalise in case stored embeddings aren't perfectly unit-norm
    probe_norm   = probe_arr   / (np.linalg.norm(probe_arr)   + 1e-9)
    gallery_norms = gallery_arr / (np.linalg.norm(gallery_arr, axis=1, keepdims=True) + 1e-9)

    similarities = gallery_norms @ probe_norm          # shape (N,)
    best_idx     = int(np.argmax(similarities))
    return best_idx, float(similarities[best_idx])


def match_with_quality(
    probe: Union[List[float], np.ndarray],
    candidates: List[Tuple[str, str, Union[List[float], np.ndarray]]],
    threshold: float = COSINE_THRESHOLD,
) -> Tuple[Optional[str], Optional[str], float, str]:
    """
    Match a probe embedding against a list of (student_id, name, embedding) candidates.
    Uses vectorised cosine similarity for speed.

    Returns:
        (student_id, student_name, cosine_score, confidence_label)
        student_id is None if no match above threshold.
    """
    if not candidates:
        return None, None, 0.0, "no_match"

    ids      = [c[0] for c in candidates]
    names    = [c[1] for c in candidates]
    gallery  = np.array([c[2] for c in candidates], dtype=np.float64)

    best_idx, best_score = batch_match_best(probe, gallery)

    label = confidence_label(best_score)

    if best_score < threshold:
        return None, None, round(best_score, 4), "no_match"

    return ids[best_idx], names[best_idx], round(best_score, 4), label
