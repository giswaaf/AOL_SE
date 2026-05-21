"""
face.py — ML Service API Routes (Versi Terintegrasi)
======================================================
Letakkan di: server/ml-service/app/api/routes/face.py

Menggantikan route bawaan nem-web/smart-attendance dengan pipeline
yang sudah menggabungkan face_recognition + Silent-Face-Anti-Spoofing.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import numpy as np
import base64
import logging
import httpx

from app.ml.attendance_pipeline import AttendancePipeline, AttendanceResult
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/face", tags=["Face Recognition"])

# Singleton pipeline — load model sekali saja saat startup
_pipeline: Optional[AttendancePipeline] = None

def get_pipeline() -> AttendancePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = AttendancePipeline()
    return _pipeline


# ── Schemas ────────────────────────────────────────────────────────────────

class VerifyAttendanceRequest(BaseModel):
    image: str           # base64 encoded image
    subject_id: str
    session_type: str = "check_in"  # "check_in" | "check_out"

class VerifyAttendanceResponse(BaseModel):
    success: bool
    is_real_face: bool
    spoofing_confidence: float
    spoofing_label: str
    student_id: Optional[str]
    student_name: Optional[str]
    recognition_confidence: float
    session_type: str
    timestamp: str
    error_message: Optional[str]

class RegisterFaceRequest(BaseModel):
    student_id: str
    image: str           # base64 encoded image

class RegisterFaceResponse(BaseModel):
    success: bool
    student_id: str
    message: str


# ── Helper: Ambil encoding siswa dari Backend API ──────────────────────────

async def fetch_student_encodings(subject_id: str) -> list:
    """
    Ambil semua face encoding siswa yang terdaftar di subject dari Backend API.
    Returns: [(student_id, student_name, np.ndarray), ...]
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.BACKEND_API_URL}/api/v1/students/encodings",
                params={"subject_id": subject_id},
                headers={"X-API-Key": settings.ML_API_KEY}
            )
            resp.raise_for_status()
            data = resp.json()

        encodings = []
        for student in data:
            if student.get("face_encoding"):
                enc = np.array(student["face_encoding"], dtype=np.float64)
                encodings.append((
                    student["_id"],
                    student["name"],
                    enc
                ))
        logger.info(f"Dimuat {len(encodings)} encoding untuk subject {subject_id}")
        return encodings

    except Exception as e:
        logger.error(f"Gagal fetch encoding dari backend: {e}")
        return []


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/verify-attendance", response_model=VerifyAttendanceResponse)
async def verify_attendance(
    request: VerifyAttendanceRequest,
    pipeline: AttendancePipeline = Depends(get_pipeline)
):
    """
    Endpoint utama untuk proses absensi.
    
    Alur:
    1. Anti-spoofing check (apakah wajah nyata?)
    2. Face encoding (128-dim vector)
    3. Face matching dengan database siswa
    4. Return hasil + trigger simpan ke MongoDB via Backend API
    """
    if request.session_type not in ("check_in", "check_out"):
        raise HTTPException(400, "session_type harus 'check_in' atau 'check_out'")

    # Ambil database encoding siswa
    known_encodings = await fetch_student_encodings(request.subject_id)

    # Jalankan pipeline
    result: AttendanceResult = pipeline.process(
        image_b64=request.image,
        known_encodings=known_encodings,
        session_type=request.session_type
    )

    # Jika berhasil, kirim ke Backend API untuk disimpan
    if result.success and result.student_id:
        await _save_attendance_to_backend(result, request.subject_id)

    return VerifyAttendanceResponse(
        success=result.success,
        is_real_face=result.is_real_face,
        spoofing_confidence=result.spoofing_confidence,
        spoofing_label=result.spoofing_label,
        student_id=result.student_id,
        student_name=result.student_name,
        recognition_confidence=result.recognition_confidence,
        session_type=result.session_type,
        timestamp=result.timestamp.isoformat(),
        error_message=result.error_message
    )


@router.post("/register", response_model=RegisterFaceResponse)
async def register_face(
    request: RegisterFaceRequest,
    pipeline: AttendancePipeline = Depends(get_pipeline)
):
    """
    Daftarkan wajah siswa baru.
    Encode wajah dan simpan ke MongoDB via Backend API.
    """
    encoding = pipeline.register_student_face(request.image)

    if encoding is None:
        raise HTTPException(
            422,
            "Tidak dapat mendeteksi wajah dalam gambar. "
            "Pastikan wajah terlihat jelas dan pencahayaan cukup."
        )

    # Simpan encoding ke backend
    success = await _save_face_encoding(request.student_id, encoding.tolist())

    if not success:
        raise HTTPException(500, "Gagal menyimpan encoding ke database.")

    return RegisterFaceResponse(
        success=True,
        student_id=request.student_id,
        message="Wajah berhasil didaftarkan."
    )


@router.get("/health")
async def health_check():
    """Status ML Service."""
    pipeline = get_pipeline()
    return {
        "status": "healthy",
        "anti_spoofing": pipeline.anti_spoof._available,
        "face_recognition": True,
    }


# ── Internal helpers ───────────────────────────────────────────────────────

async def _save_attendance_to_backend(result: AttendanceResult, subject_id: str):
    """Kirim record absensi ke Backend API untuk disimpan ke MongoDB."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{settings.BACKEND_API_URL}/api/v1/attendance/record",
                json={
                    "student_id": result.student_id,
                    "subject_id": subject_id,
                    "session_type": result.session_type,
                    "timestamp": result.timestamp.isoformat(),
                    "confidence": result.recognition_confidence,
                },
                headers={"X-API-Key": settings.ML_API_KEY}
            )
    except Exception as e:
        logger.error(f"Gagal simpan absensi ke backend: {e}")


async def _save_face_encoding(student_id: str, encoding: list) -> bool:
    """Simpan face encoding ke database via Backend API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(
                f"{settings.BACKEND_API_URL}/api/v1/students/{student_id}/encoding",
                json={"face_encoding": encoding},
                headers={"X-API-Key": settings.ML_API_KEY}
            )
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Gagal simpan face encoding: {e}")
        return False
