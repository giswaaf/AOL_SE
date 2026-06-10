import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import numpy as np

# We can import face_route because its directory (root_dir) is in sys.path
import face_route
from face_route import router, get_pipeline
from attendance_pipeline import AttendanceResult

# Create a dummy FastAPI app to mount the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_check():
    # Mock pipeline anti-spoof availability
    mock_pipeline = MagicMock()
    mock_pipeline.anti_spoof._available = True
    
    with patch('face_route.get_pipeline', return_value=mock_pipeline):
        response = client.get("/face/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["anti_spoofing"] is True
        assert data["face_recognition"] is True


@patch('face_route.fetch_student_encodings')
@patch('face_route._save_attendance_to_backend')
def test_verify_attendance_success(mock_save, mock_fetch):
    # Setup mocks
    mock_fetch.return_value = [("student123", "John Doe", np.zeros(128))]
    mock_save.return_value = AsyncMock()

    mock_result = AttendanceResult(
        success=True,
        is_real_face=True,
        spoofing_confidence=0.9,
        spoofing_label="Real",
        student_id="student123",
        student_name="John Doe",
        recognition_confidence=0.85,
        session_type="check_in",
        timestamp=datetime.utcnow()
    )

    mock_pipeline = MagicMock()
    mock_pipeline.process.return_value = mock_result

    with patch('face_route.get_pipeline', return_value=mock_pipeline):
        payload = {
            "image": "dummy_base64_data",
            "subject_id": "subject789",
            "session_type": "check_in"
        }
        response = client.post("/face/verify-attendance", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["student_id"] == "student123"
        assert data["student_name"] == "John Doe"
        assert data["is_real_face"] is True


@patch('face_route._save_face_encoding')
def test_register_face_success(mock_save):
    mock_save.return_value = AsyncMock()
    mock_save.return_value = True

    mock_pipeline = MagicMock()
    mock_pipeline.register_student_face.return_value = np.zeros(128)

    with patch('face_route.get_pipeline', return_value=mock_pipeline):
        payload = {
            "student_id": "student_new",
            "image": "dummy_base64_data"
        }
        response = client.post("/face/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["student_id"] == "student_new"
        assert "berhasil didaftarkan" in data["message"]


@patch('face_route._save_face_encoding')
def test_register_face_fail_no_face(mock_save):
    mock_pipeline = MagicMock()
    mock_pipeline.register_student_face.return_value = None

    with patch('face_route.get_pipeline', return_value=mock_pipeline):
        payload = {
            "student_id": "student_new",
            "image": "dummy_base64_data"
        }
        response = client.post("/face/register", json=payload)
        assert response.status_code == 422
        assert "Tidak dapat mendeteksi wajah" in response.json()["detail"]
