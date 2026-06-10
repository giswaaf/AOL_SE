import pytest
import numpy as np
import cv2
import base64
from unittest.mock import MagicMock, patch
from attendance_pipeline import (
    AntiSpoofingChecker,
    FaceRecognizer,
    AttendancePipeline,
    AttendanceResult
)

# Dummy base64 encoded image (a small black square)
dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
_, buffer = cv2.imencode('.jpg', dummy_img)
DUMMY_B64 = base64.b64encode(buffer).decode('utf-8')


def test_decode_image():
    pipeline = AttendancePipeline()
    img = pipeline.decode_image(DUMMY_B64)
    assert isinstance(img, np.ndarray)
    assert img.shape == (100, 100, 3)


def test_decode_image_invalid():
    pipeline = AttendancePipeline()
    with pytest.raises(Exception):
        pipeline.decode_image("invalid_base64_string")


@patch('attendance_pipeline.ANTI_SPOOFING_AVAILABLE', False)
def test_anti_spoofing_checker_unavailable():
    checker = AntiSpoofingChecker()
    # If not available, it should bypass and return is_real=True
    res = checker.check(dummy_img)
    assert res["is_real"] is True
    assert "bypass" in res["label"].lower()


@patch('attendance_pipeline.face_recognition')
def test_face_recognizer_encode_no_face(mock_face_rec):
    mock_face_rec.face_locations.return_value = []
    recognizer = FaceRecognizer()
    encoding = recognizer.encode_face(dummy_img)
    assert encoding is None


@patch('attendance_pipeline.face_recognition')
def test_face_recognizer_encode_success(mock_face_rec):
    mock_face_rec.face_locations.return_value = [(0, 100, 100, 0)]
    mock_face_rec.face_encodings.return_value = [np.zeros(128)]
    recognizer = FaceRecognizer()
    encoding = recognizer.encode_face(dummy_img)
    assert encoding is not None
    assert len(encoding) == 128


def test_face_recognizer_match_empty_database():
    recognizer = FaceRecognizer()
    student_id, student_name, confidence = recognizer.match_face(np.zeros(128), [])
    assert student_id is None
    assert student_name is None
    assert confidence == 0.0


@patch('attendance_pipeline.face_recognition.face_distance')
def test_face_recognizer_match_success(mock_face_dist):
    mock_face_dist.return_value = np.array([0.2])  # very close distance (match)
    recognizer = FaceRecognizer()
    known = [("1", "John Doe", np.zeros(128))]
    student_id, student_name, confidence = recognizer.match_face(np.zeros(128), known)
    assert student_id == "1"
    assert student_name == "John Doe"
    assert confidence > 0.7


@patch('attendance_pipeline.face_recognition.face_distance')
def test_face_recognizer_match_no_match(mock_face_dist):
    mock_face_dist.return_value = np.array([0.9])  # far distance (no match)
    recognizer = FaceRecognizer()
    known = [("1", "John Doe", np.zeros(128))]
    student_id, student_name, confidence = recognizer.match_face(np.zeros(128), known)
    assert student_id is None
    assert student_name is None
    assert confidence == 0.0


@patch.object(AntiSpoofingChecker, 'check')
@patch.object(FaceRecognizer, 'encode_face')
@patch.object(FaceRecognizer, 'match_face')
def test_pipeline_process_success(mock_match, mock_encode, mock_spoof):
    mock_spoof.return_value = {"is_real": True, "confidence": 0.95, "label": "Real"}
    mock_encode.return_value = np.zeros(128)
    mock_match.return_value = ("123", "Alice", 0.9)

    pipeline = AttendancePipeline()
    result = pipeline.process(DUMMY_B64, [("123", "Alice", np.zeros(128))])
    
    assert result.success is True
    assert result.student_id == "123"
    assert result.student_name == "Alice"
    assert result.is_real_face is True


@patch.object(AntiSpoofingChecker, 'check')
def test_pipeline_process_spoof_detected(mock_spoof):
    mock_spoof.return_value = {"is_real": False, "confidence": 0.99, "label": "Fake"}

    pipeline = AttendancePipeline()
    result = pipeline.process(DUMMY_B64, [])
    
    assert result.success is False
    assert result.is_real_face is False
    assert "Spoofing terdeteksi" in result.error_message


@patch.object(FaceRecognizer, 'encode_face')
def test_pipeline_register_student_face_success(mock_encode):
    mock_encode.return_value = np.zeros(128)
    pipeline = AttendancePipeline()
    encoding = pipeline.register_student_face(DUMMY_B64)
    assert encoding is not None
    assert len(encoding) == 128
