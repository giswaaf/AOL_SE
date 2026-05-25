from typing import List
import cv2
import numpy as np
import face_recognition

MIN_FACE_AREA_RATIO = 0.05  # face must cover at least 5% of image
NUM_JITTERS = 1  # 1 is default, fast and accurate enough for real-time



def get_face_embedding(face_img: np.ndarray) -> List[float]:
    """Embedding from face crop. Expects RGB (e.g. from PIL/API)."""
    if face_img.ndim == 2:
        gray = face_img
    else:
        gray = cv2.cvtColor(face_img, cv2.COLOR_RGB2GRAY)
        
    # Improvement: Apply histogram equalization to normalize contrast and lighting
    gray = cv2.equalizeHist(gray)
    
    resized = cv2.resize(gray, (96, 96))
    emb = resized.flatten().astype("float32")
    emb /= np.linalg.norm(emb)
    return emb.tolist()

