import base64
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np

# ── Anti-spoofing (unchanged) ─────────────────────────────────────────────
sys.path.append(str(Path(__file__).parent.parent / "anti_spoof_src"))

try:
    from anti_spoof_predict import AntiSpoofPredict
    from generate_patches import CropImage
    from utility import parse_model_name
    ANTI_SPOOFING_AVAILABLE = True
except ImportError:
    ANTI_SPOOFING_AVAILABLE = False
    logging.warning(
        "Anti-spoofing module tidak ditemukan. "
        "Clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing "
        "dan copy folder src/ ke app/anti_spoof_src/"
    )

# ── Improved embedding + matching ────────────────────────────────────────
from app.ml.face_encoder import get_face_embedding, get_averaged_embedding
from app.ml.face_matcher import (
    match_with_quality,
    COSINE_THRESHOLD,
    confidence_label,
)
from app.ml.face_detector import detect_faces

logger = logging.getLogger(__name__)

ANTI_SPOOF_MODEL_DIR = Path(__file__).parent.parent.parent / "resources" / "anti_spoof_models"
DETECTION_MODEL_DIR  = Path(__file__).parent.parent.parent / "resources" / "detection_model"

# Minimum frames required for a good multi-frame enrollment
MIN_ENROLLMENT_FRAMES = 5
RECOMMENDED_ENROLLMENT_FRAMES = 15


@dataclass
class AttendanceResult:
    """Hasil pipeline absensi lengkap."""
    success: bool
    # Anti-spoofing
    is_real_face: bool
    spoofing_confidence: float
    spoofing_label: str
    # Face recognition
    student_id: Optional[str]
    student_name: Optional[str]
    recognition_confidence: float
    confidence_label: str = "no_match"   # NEW: "high" | "medium" | "low" | "no_match"
    # Meta
    session_type: str = "check_in"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


# ── Anti-spoofing (unchanged from original) ───────────────────────────────

class AntiSpoofingChecker:
    """Wrapper for minivision-ai/Silent-Face-Anti-Spoofing."""

    def __init__(self, model_dir: Path = ANTI_SPOOF_MODEL_DIR, device_id: int = 0):
        self.model_dir = model_dir
        self.device_id = device_id
        self._model = None
        self._crop_image = None
        self._available = ANTI_SPOOFING_AVAILABLE and model_dir.exists()
        if self._available:
            self._load_model()
        else:
            logger.warning("Anti-spoofing dinonaktifkan (model tidak tersedia).")

    def _load_model(self):
        try:
            self._model = AntiSpoofPredict(self.device_id)
            self._crop_image = CropImage()
            logger.info("✅ Anti-spoofing model berhasil dimuat.")
        except Exception as e:
            self._available = False
            logger.error(f"❌ Gagal load model anti-spoofing: {e}")

    def check(self, image_bgr: np.ndarray) -> dict:
        if not self._available:
            return {"is_real": True, "confidence": 1.0, "label": "Unknown (bypass)"}

        try:
            image_bbox = self._model.get_bbox(image_bgr)
            if image_bbox is None:
                return {"is_real": False, "confidence": 0.0, "label": "No Face Detected"}

            prediction = np.zeros((1, 3))
            for model_name in self.model_dir.iterdir():
                if not model_name.name.endswith(".pkl"):
                    continue
                h_input, w_input, model_type, scale = parse_model_name(model_name.name)
                param = {
                    "org_img": image_bgr,
                    "bbox": image_bbox,
                    "scale": scale,
                    "out_w": w_input,
                    "out_h": h_input,
                    "crop": scale is None,
                }
                img = self._crop_image.crop(**param)
                prediction += self._model.predict(img, str(model_name))

            label = np.argmax(prediction)
            is_real = (label == 1)
            confidence = float(prediction[0][label] / prediction.sum())
            return {
                "is_real": bool(is_real),
                "confidence": round(confidence, 4),
                "label": "Real" if is_real else "Fake",
            }

        except Exception as e:
            logger.error(f"Error anti-spoofing: {e}")
            return {"is_real": False, "confidence": 0.0, "label": f"Error: {str(e)}"}


# ── Improved FaceRecognizer ───────────────────────────────────────────────

class FaceRecognizer:
    """
    Improved face recognizer using ArcFace embeddings (512-dim) instead of
    the old dlib-based HOG pipeline.

    Key differences:
    - encode_face() uses InsightFace ArcFace → 512-dim vector
    - match_face() uses vectorised cosine similarity with quality tiers
    - Supports averaged embeddings from multiple enrollment frames
    """

    def _crop_face_from_image(self, image_rgb: np.ndarray) -> Optional[np.ndarray]:
        """Detect and crop the largest face from an image."""
        faces = detect_faces(image_rgb)
        if not faces:
            return None

        # Pick largest face by area
        best = max(faces, key=lambda f: (f[2] - f[0]) * (f[1] - f[3]))
        top, right, bottom, left = best

        # Safety clamp
        h, w = image_rgb.shape[:2]
        top    = max(0, top)
        left   = max(0, left)
        bottom = min(h, bottom)
        right  = min(w, right)

        if bottom <= top or right <= left:
            return None

        return image_rgb[top:bottom, left:right]

    def encode_face(self, image_rgb: np.ndarray) -> Optional[np.ndarray]:
        """
        Encode a single image to a 512-dim ArcFace embedding.
        Returns np.ndarray or None if no face found.
        """
        crop = self._crop_face_from_image(image_rgb)
        if crop is None:
            logger.debug("No face detected for encoding.")
            return None

        try:
            # face_encoder.py expects BGR input; crop is RGB — convert
            bgr_crop = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
            emb = get_face_embedding(bgr_crop)
            return np.array(emb, dtype=np.float32)
        except Exception as e:
            logger.error(f"Encoding error: {e}")
            return None

    def encode_faces_multi(
        self, images_rgb: List[np.ndarray]
    ) -> Optional[np.ndarray]:
        """
        Generate an averaged embedding from multiple images (multi-frame enrollment).
        Returns a single 512-dim vector representing the student's face centroid.
        """
        crops = []
        for img in images_rgb:
            crop = self._crop_face_from_image(img)
            if crop is not None:
                crops.append(cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))

        if len(crops) < MIN_ENROLLMENT_FRAMES:
            logger.warning(
                f"Only {len(crops)} valid face crops out of {len(images_rgb)} frames. "
                f"Minimum recommended: {MIN_ENROLLMENT_FRAMES}."
            )

        if not crops:
            return None

        try:
            emb = get_averaged_embedding(crops)
            return np.array(emb, dtype=np.float32)
        except Exception as e:
            logger.error(f"Multi-frame encoding error: {e}")
            return None

    def match_face(
        self,
        unknown_encoding: np.ndarray,
        known_encodings: List[Tuple[str, str, np.ndarray]],
    ) -> Tuple[Optional[str], Optional[str], float]:
        """
        Match against database using vectorised cosine similarity.
        Returns (student_id, name, confidence). student_id=None if no match.
        """
        if not known_encodings:
            return None, None, 0.0

        student_id, name, score, conf_label = match_with_quality(
            unknown_encoding, known_encodings, threshold=COSINE_THRESHOLD
        )

        if student_id:
            logger.info(f"✅ Match: {name} (score: {score:.3f}, tier: {conf_label})")
        else:
            logger.info(f"No match (best score: {score:.3f})")

        return student_id, name, score


# ── Main Pipeline ─────────────────────────────────────────────────────────

class AttendancePipeline:
    """
    Pipeline utama:
      1. Anti-spoofing (Silent-Face)
      2. Face recognition (ArcFace 512-dim via InsightFace)
      3. Return AttendanceResult
    """

    SPOOFING_THRESHOLD = 0.6

    def __init__(self):
        self.anti_spoof = AntiSpoofingChecker()
        self.recognizer = FaceRecognizer()
        logger.info("🚀 AttendancePipeline (ArcFace) siap.")

    def decode_image(self, image_b64: str) -> np.ndarray:
        """Decode base64 image → BGR numpy array."""
        img_bytes = base64.b64decode(image_b64.split(",")[-1])
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        image_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("Gagal decode gambar. Format tidak valid.")
        return image_bgr

    def process(
        self,
        image_b64: str,
        known_encodings: List[Tuple[str, str, np.ndarray]],
        session_type: str = "check_in",
    ) -> AttendanceResult:
        """Full attendance pipeline from a single base64 image."""
        timestamp = datetime.utcnow()

        # Step 0: Decode
        try:
            image_bgr = self.decode_image(image_b64)
        except ValueError as e:
            return AttendanceResult(
                success=False, is_real_face=False, spoofing_confidence=0,
                spoofing_label="Error", student_id=None, student_name=None,
                recognition_confidence=0, session_type=session_type,
                timestamp=timestamp, error_message=str(e)
            )

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Step 1: Anti-spoofing
        spoof_result = self.anti_spoof.check(image_bgr)
        is_real    = spoof_result["is_real"]
        spoof_conf = spoof_result["confidence"]
        spoof_label = spoof_result["label"]

        logger.info(f"[Anti-Spoofing] {spoof_label} (conf: {spoof_conf:.2%})")

        if not is_real and spoof_conf > self.SPOOFING_THRESHOLD:
            return AttendanceResult(
                success=False, is_real_face=False,
                spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
                student_id=None, student_name=None, recognition_confidence=0,
                confidence_label="no_match",
                session_type=session_type, timestamp=timestamp,
                error_message="Spoofing terdeteksi: wajah tidak nyata.",
            )

        # Step 2: Encode
        encoding = self.recognizer.encode_face(image_rgb)
        if encoding is None:
            return AttendanceResult(
                success=False, is_real_face=True,
                spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
                student_id=None, student_name=None, recognition_confidence=0,
                confidence_label="no_match",
                session_type=session_type, timestamp=timestamp,
                error_message="Tidak ada wajah terdeteksi dalam frame.",
            )

        # Step 3: Match
        student_id, student_name, recog_conf = self.recognizer.match_face(
            encoding, known_encodings
        )
        conf_tier = confidence_label(recog_conf) if student_id else "no_match"

        if student_id is None:
            return AttendanceResult(
                success=False, is_real_face=True,
                spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
                student_id=None, student_name=None,
                recognition_confidence=recog_conf,
                confidence_label=conf_tier,
                session_type=session_type, timestamp=timestamp,
                error_message="Wajah tidak dikenali dalam database.",
            )

        logger.info(
            f"✅ Absensi berhasil: {student_name} | Sesi: {session_type} | "
            f"Confidence: {recog_conf:.2%} ({conf_tier})"
        )
        return AttendanceResult(
            success=True, is_real_face=True,
            spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
            student_id=student_id, student_name=student_name,
            recognition_confidence=recog_conf,
            confidence_label=conf_tier,
            session_type=session_type, timestamp=timestamp,
        )

    def register_student_face(self, image_b64: str) -> Optional[np.ndarray]:
        """
        Single-image registration (backward compat).
        Prefer register_student_face_from_frames() for better accuracy.
        """
        try:
            image_bgr = self.decode_image(image_b64)
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            encoding  = self.recognizer.encode_face(image_rgb)
            if encoding is None:
                logger.warning("Gagal encode wajah saat registrasi.")
                return None
            logger.info("✅ Single-image face encoded for registration.")
            return encoding
        except Exception as e:
            logger.error(f"Error saat registrasi wajah: {e}")
            return None

    def register_student_face_from_frames(
        self, frames_b64: List[str]
    ) -> Optional[np.ndarray]:
        """
        Multi-frame registration from a live video enrollment session.

        Accepts 5–30 base64 frames captured during a head-turn sequence
        (front → left → right → front). Produces an averaged ArcFace embedding
        that is significantly more robust than a single still photo.

        Returns 512-dim np.ndarray or None on failure.
        """
        if not frames_b64:
            logger.error("No frames provided for multi-frame registration.")
            return None

        images_rgb = []
        for i, b64 in enumerate(frames_b64):
            try:
                bgr = self.decode_image(b64)
                images_rgb.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            except Exception as e:
                logger.warning(f"Skipping frame {i}: {e}")

        if not images_rgb:
            logger.error("All frames failed to decode.")
            return None

        encoding = self.recognizer.encode_faces_multi(images_rgb)
        if encoding is None:
            logger.warning("Multi-frame encoding failed — no valid face crops.")
            return None

        logger.info(
            f"✅ Multi-frame enrollment: averaged from {len(images_rgb)} frames."
        )
        return encoding
