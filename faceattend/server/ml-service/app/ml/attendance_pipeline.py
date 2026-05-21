"""
attendance_pipeline.py
=======================
INTI INTEGRASI — Menggabungkan 3 repository:
  1. ageitgey/face_recognition  → Face encoding & matching
  2. minivision-ai/Silent-Face-Anti-Spoofing → Anti-spoofing
  3. nem-web/smart-attendance   → Web app & database layer

Letakkan file ini di: server/ml-service/app/ml/attendance_pipeline.py
"""

import cv2
import numpy as np
import face_recognition
import base64
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Tuple
from pathlib import Path

# Import anti-spoofing dari Silent-Face-Anti-Spoofing
# (pastikan folder src/ sudah dicopy ke app/anti_spoof_src/)
import sys
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

logger = logging.getLogger(__name__)

# ── Path ke model anti-spoofing ────────────────────────────────────────────
ANTI_SPOOF_MODEL_DIR = Path(__file__).parent.parent.parent / "resources" / "anti_spoof_models"
DETECTION_MODEL_DIR  = Path(__file__).parent.parent.parent / "resources" / "detection_model"


@dataclass
class AttendanceResult:
    """Hasil pipeline absensi lengkap."""
    success: bool
    # Anti-spoofing
    is_real_face: bool
    spoofing_confidence: float
    spoofing_label: str          # "Real" atau "Fake"
    # Face recognition
    student_id: Optional[str]
    student_name: Optional[str]
    recognition_confidence: float  # 0-1, makin tinggi makin yakin
    # Meta
    session_type: str            # "check_in" atau "check_out"
    timestamp: datetime
    error_message: Optional[str] = None


class AntiSpoofingChecker:
    """
    Wrapper untuk minivision-ai/Silent-Face-Anti-Spoofing.
    Mendeteksi apakah wajah di frame adalah wajah nyata atau spoofing
    (foto, layar, topeng silikon, dll).
    """

    def __init__(self, model_dir: Path = ANTI_SPOOF_MODEL_DIR,
                 device_id: int = 0):
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
        """Load model anti-spoofing."""
        try:
            self._model = AntiSpoofPredict(self.device_id)
            self._crop_image = CropImage()
            logger.info("✅ Anti-spoofing model berhasil dimuat.")
        except Exception as e:
            self._available = False
            logger.error(f"❌ Gagal load model anti-spoofing: {e}")

    def check(self, image_bgr: np.ndarray) -> dict:
        """
        Periksa apakah wajah nyata.

        Args:
            image_bgr: Frame dari OpenCV (BGR format)

        Returns:
            dict: {
                "is_real": bool,
                "confidence": float (0-1),
                "label": "Real" | "Fake" | "Unknown"
            }
        """
        if not self._available:
            # Jika modul tidak tersedia, anggap real (fallback)
            logger.warning("Anti-spoofing tidak tersedia, skip check.")
            return {"is_real": True, "confidence": 1.0, "label": "Unknown (bypass)"}

        try:
            image_cropper = self._crop_image
            model_test = self._model

            # Resize untuk model
            image_bbox = model_test.get_bbox(image_bgr)
            if image_bbox is None:
                return {"is_real": False, "confidence": 0.0, "label": "No Face Detected"}

            prediction = np.zeros((1, 3))

            # Multi-scale test (dari Silent-Face-Anti-Spoofing/test.py)
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
                    "crop": True if scale is None else False,
                }
                img = image_cropper.crop(**param)
                prediction += model_test.predict(img, str(model_name))

            # Interpretasi hasil
            label = np.argmax(prediction)
            # label 1 = Real, label 0 = Fake
            is_real = (label == 1)
            confidence = float(prediction[0][label] / prediction.sum())

            return {
                "is_real": bool(is_real),
                "confidence": round(confidence, 4),
                "label": "Real" if is_real else "Fake"
            }

        except Exception as e:
            logger.error(f"Error anti-spoofing: {e}")
            return {"is_real": False, "confidence": 0.0, "label": f"Error: {str(e)}"}


class FaceRecognizer:
    """
    Wrapper untuk ageitgey/face_recognition.
    Encode wajah dan bandingkan dengan database encoding.
    """

    # Threshold jarak wajah (lebih kecil = lebih ketat)
    TOLERANCE = 0.55

    def encode_face(self, image_rgb: np.ndarray) -> Optional[np.ndarray]:
        """
        Encode wajah dari gambar menjadi 128-dim vector.

        Args:
            image_rgb: Gambar RGB (numpy array)

        Returns:
            np.ndarray (128,) atau None jika tidak ada wajah terdeteksi
        """
        face_locations = face_recognition.face_locations(image_rgb, model="hog")
        if not face_locations:
            logger.debug("Tidak ada wajah terdeteksi dalam gambar.")
            return None

        encodings = face_recognition.face_encodings(image_rgb, face_locations)
        if not encodings:
            return None

        # Ambil encoding wajah pertama (terbesar) saja
        return encodings[0]

    def match_face(
        self,
        unknown_encoding: np.ndarray,
        known_encodings: List[Tuple[str, str, np.ndarray]]
    ) -> Tuple[Optional[str], Optional[str], float]:
        """
        Cocokkan encoding wajah dengan database.

        Args:
            unknown_encoding: 128-dim vector wajah yang difoto
            known_encodings: List of (student_id, student_name, encoding)

        Returns:
            Tuple: (student_id, student_name, confidence)
                   student_id = None jika tidak cocok
        """
        if not known_encodings:
            return None, None, 0.0

        ids      = [e[0] for e in known_encodings]
        names    = [e[1] for e in known_encodings]
        encodings = [e[2] for e in known_encodings]

        # Hitung jarak ke semua encoding yang diketahui
        distances = face_recognition.face_distance(encodings, unknown_encoding)
        best_idx  = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist > self.TOLERANCE:
            logger.info(f"Wajah tidak cocok (jarak terbaik: {best_dist:.3f})")
            return None, None, 0.0

        # Konversi jarak ke confidence (0-1, makin tinggi makin yakin)
        confidence = round(1.0 - best_dist, 4)
        logger.info(
            f"✅ Match: {names[best_idx]} (confidence: {confidence:.2%})"
        )
        return ids[best_idx], names[best_idx], confidence


class AttendancePipeline:
    """
    Pipeline utama yang menggabungkan ketiga komponen:
      1. AntiSpoofingChecker  (Silent-Face-Anti-Spoofing)
      2. FaceRecognizer       (face_recognition)
      3. Hasil dikirim ke Backend API untuk disimpan ke MongoDB
    """

    # Threshold minimum confidence anti-spoofing untuk dianggap "real"
    SPOOFING_THRESHOLD = 0.6

    def __init__(self):
        self.anti_spoof  = AntiSpoofingChecker()
        self.recognizer  = FaceRecognizer()
        logger.info("🚀 AttendancePipeline siap.")

    def decode_image(self, image_b64: str) -> np.ndarray:
        """Decode base64 image string menjadi numpy array BGR."""
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
        session_type: str = "check_in"
    ) -> AttendanceResult:
        """
        Proses absensi lengkap dari foto base64.

        Args:
            image_b64: Foto dari webcam (base64 string)
            known_encodings: Database encoding siswa [(id, name, encoding), ...]
            session_type: "check_in" atau "check_out"

        Returns:
            AttendanceResult lengkap
        """
        timestamp = datetime.utcnow()

        # ── Step 0: Decode gambar ──────────────────────────────────────────
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

        # ── Step 1: Anti-Spoofing ──────────────────────────────────────────
        spoof_result = self.anti_spoof.check(image_bgr)
        is_real      = spoof_result["is_real"]
        spoof_conf   = spoof_result["confidence"]
        spoof_label  = spoof_result["label"]

        logger.info(f"[Anti-Spoofing] {spoof_label} (conf: {spoof_conf:.2%})")

        if not is_real and spoof_conf > self.SPOOFING_THRESHOLD:
            # Wajah palsu terdeteksi — tolak absensi
            return AttendanceResult(
                success=False, is_real_face=False,
                spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
                student_id=None, student_name=None, recognition_confidence=0,
                session_type=session_type, timestamp=timestamp,
                error_message="Spoofing terdeteksi: wajah tidak nyata."
            )

        # ── Step 2: Face Encoding ──────────────────────────────────────────
        encoding = self.recognizer.encode_face(image_rgb)
        if encoding is None:
            return AttendanceResult(
                success=False, is_real_face=True,
                spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
                student_id=None, student_name=None, recognition_confidence=0,
                session_type=session_type, timestamp=timestamp,
                error_message="Tidak ada wajah terdeteksi dalam frame."
            )

        # ── Step 3: Face Matching ──────────────────────────────────────────
        student_id, student_name, recog_conf = self.recognizer.match_face(
            encoding, known_encodings
        )

        if student_id is None:
            return AttendanceResult(
                success=False, is_real_face=True,
                spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
                student_id=None, student_name=None,
                recognition_confidence=recog_conf,
                session_type=session_type, timestamp=timestamp,
                error_message="Wajah tidak dikenali dalam database."
            )

        # ── Step 4: Sukses ─────────────────────────────────────────────────
        logger.info(
            f"✅ Absensi berhasil: {student_name} | "
            f"Sesi: {session_type} | Waktu: {timestamp}"
        )
        return AttendanceResult(
            success=True, is_real_face=True,
            spoofing_confidence=spoof_conf, spoofing_label=spoof_label,
            student_id=student_id, student_name=student_name,
            recognition_confidence=recog_conf,
            session_type=session_type, timestamp=timestamp
        )

    def register_student_face(self, image_b64: str) -> Optional[np.ndarray]:
        """
        Encode wajah siswa baru untuk disimpan ke database.

        Args:
            image_b64: Foto wajah siswa (base64)

        Returns:
            np.ndarray (128,) encoding, atau None jika gagal
        """
        try:
            image_bgr = self.decode_image(image_b64)
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            encoding  = self.recognizer.encode_face(image_rgb)

            if encoding is None:
                logger.warning("Gagal encode wajah saat registrasi.")
                return None

            logger.info("✅ Wajah siswa berhasil di-encode untuk registrasi.")
            return encoding

        except Exception as e:
            logger.error(f"Error saat registrasi wajah: {e}")
            return None
