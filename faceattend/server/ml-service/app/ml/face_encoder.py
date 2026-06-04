from __future__ import annotations

import logging
from typing import List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Runtime backend selection ─────────────────────────────────────────────
# We try InsightFace (ArcFace) first; fallback to DeepFace (Facenet512)
# if InsightFace is not installed. Both produce 512-dim L2-normalized vectors.

_insightface_app = None   # lazy-loaded InsightFace app
_backend: str = "unknown"


def _load_insightface():
    """Lazy-load InsightFace Buffalo_l model (ArcFace backbone)."""
    global _insightface_app, _backend
    if _insightface_app is not None:
        return _insightface_app

    try:
        import insightface
        from insightface.app import FaceAnalysis

        app = FaceAnalysis(
            name="buffalo_l",          # best accuracy; use "buffalo_sc" for speed
            providers=["CPUExecutionProvider"],
            allowed_modules=["detection", "recognition"],
        )
        app.prepare(ctx_id=0, det_size=(640, 640))
        _insightface_app = app
        _backend = "insightface_arcface"
        logger.info("✅ InsightFace ArcFace (buffalo_l) loaded.")
        return app

    except Exception as e:
        logger.warning(f"InsightFace not available ({e}), falling back to DeepFace.")
        _backend = "deepface_facenet512"
        return None


def _get_backend() -> str:
    _load_insightface()
    return _backend


# ── Preprocessing helpers ─────────────────────────────────────────────────

def _preprocess_face(face_img: np.ndarray) -> np.ndarray:
    """
    Normalize a face crop for embedding:
    1. Resize to 112×112 (ArcFace standard input)
    2. CLAHE equalisation (handles backlight / poor lighting)
    3. Convert to RGB (InsightFace expects RGB)
    """
    if face_img is None or face_img.size == 0:
        raise ValueError("Empty face image received for preprocessing.")

    # Convert grayscale → BGR if needed
    if face_img.ndim == 2:
        face_img = cv2.cvtColor(face_img, cv2.COLOR_GRAY2BGR)

    # Resize
    resized = cv2.resize(face_img, (112, 112), interpolation=cv2.INTER_LINEAR)

    # CLAHE on L-channel (improves recognition under uneven lighting)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # InsightFace/DeepFace both want RGB
    return cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)


def _embed_insightface(face_img_rgb: np.ndarray) -> Optional[List[float]]:
    """
    Get ArcFace embedding via InsightFace.
    face_img_rgb: RGB uint8 image (any size — InsightFace runs its own detector)
    Returns 512-dim L2-normalised vector, or None on failure.
    """
    app = _load_insightface()
    if app is None:
        return None

    try:
        # InsightFace expects RGB; detects faces internally
        faces = app.get(face_img_rgb)
        if not faces:
            logger.debug("InsightFace found no face in crop.")
            return None

        # Pick highest-confidence detection
        face = max(faces, key=lambda f: f.det_score)
        emb = face.normed_embedding  # Already L2-normalised 512-dim

        if emb is None or len(emb) != 512:
            return None

        return emb.astype("float32").tolist()

    except Exception as e:
        logger.error(f"InsightFace embedding error: {e}")
        return None


def _embed_deepface(face_img_rgb: np.ndarray) -> Optional[List[float]]:
    """
    Get Facenet512 embedding via DeepFace (fallback).
    Returns 512-dim L2-normalised vector, or None on failure.
    """
    try:
        from deepface import DeepFace
        import cv2 as _cv2

        bgr = _cv2.cvtColor(face_img_rgb, _cv2.COLOR_RGB2BGR)
        result = DeepFace.represent(
            img_path=bgr,
            model_name="Facenet512",
            detector_backend="skip",   # we already have a cropped face
            enforce_detection=False,
            align=False,               # pre-aligned via _preprocess_face
        )
        if not result:
            return None

        emb = np.array(result[0]["embedding"], dtype="float32")
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm

        return emb.tolist()

    except Exception as e:
        logger.error(f"DeepFace embedding error: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────

def get_face_embedding(face_img: np.ndarray) -> List[float]:
    """
    Primary entry point — returns a 512-dim L2-normalised embedding.

    Drop-in replacement for the old pixel-flatten approach, but INCOMPATIBLE
    with stored embeddings from the old encoder (different dimensionality &
    semantic space). Re-enrol all students after deploying this file.

    Args:
        face_img: Cropped face image, BGR or grayscale, any reasonable size.

    Returns:
        List[float] of length 512.

    Raises:
        ValueError: If no face can be embedded (empty image, total failure).
    """
    processed = _preprocess_face(face_img)

    backend = _get_backend()

    if backend == "insightface_arcface":
        emb = _embed_insightface(processed)
    else:
        emb = _embed_deepface(processed)

    # Last-resort: if model pipeline failed, try the other backend
    if emb is None:
        logger.warning("Primary backend failed, trying secondary.")
        emb = _embed_deepface(processed) if backend == "insightface_arcface" else None

    if emb is None:
        raise ValueError(
            "Could not generate face embedding — face not detected or model error."
        )

    logger.debug(f"Embedding generated via {backend}, dim={len(emb)}")
    return emb


def get_averaged_embedding(face_crops: list[np.ndarray]) -> List[float]:
    """
    Generate a single representative embedding by averaging embeddings
    from multiple face crops (e.g., from a live-video enrollment session).

    This is the key accuracy improvement for the live-video registration flow:
    averaging embeddings from 10-20 frames at different angles produces a
    centroid that generalises far better than a single photo.

    Args:
        face_crops: List of BGR/gray face crop arrays (at least 1).

    Returns:
        512-dim L2-normalised averaged embedding as List[float].

    Raises:
        ValueError: If fewer than 1 valid embedding could be computed.
    """
    if not face_crops:
        raise ValueError("No face crops provided.")

    embeddings = []
    for i, crop in enumerate(face_crops):
        try:
            emb = get_face_embedding(crop)
            embeddings.append(np.array(emb, dtype="float32"))
        except Exception as e:
            logger.warning(f"Skipping crop {i}: {e}")

    if not embeddings:
        raise ValueError("All face crops failed to embed.")

    # Average then re-normalise
    avg = np.mean(np.stack(embeddings, axis=0), axis=0)
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm

    logger.info(
        f"Averaged embedding from {len(embeddings)}/{len(face_crops)} valid crops."
    )
    return avg.tolist()
