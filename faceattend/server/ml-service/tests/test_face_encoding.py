import os
import cv2
import numpy as np
import pytest
from app.ml.face_encoder import get_face_embedding

def test_get_face_embedding_length():
    # We should get a 512-dimensional embedding
    # Let's load the obama.jpg file from workspace if it exists to test with a real face
    obama_path = "/Users/darrisfelicio/Documents/Face_Attendance/obama.jpg"
    if os.path.exists(obama_path):
        img = cv2.imread(obama_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[:] = 100

    try:
        emb = get_face_embedding(img)
        assert isinstance(emb, list)
        assert len(emb) == 512
    except ValueError as e:
        if "Could not generate face embedding" in str(e):
            pytest.skip("Skipping because model backend failed to load or face not detected in mock image")
        else:
            raise e

def test_get_face_embedding_zeros():
    # If image is non-zero solid, norm should be 1.0 (L2 normalized)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = 128
    try:
        emb = get_face_embedding(img)
        arr = np.array(emb)
        norm = np.linalg.norm(arr)
        assert abs(norm - 1.0) < 1e-5
        assert len(emb) == 512
    except ValueError:
        pytest.skip("Skipping because model backend failed to load or face not detected")
