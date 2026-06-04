import httpx
import base64
import numpy as np
import cv2

# create a dummy image (e.g., a white square, or an actual random face if needed)
# actually, let's create a random array and encode as jpg
img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
_, buffer = cv2.imencode('.jpg', img)
b64 = base64.b64encode(buffer).decode('utf-8')

resp = httpx.post("http://localhost:8001/api/ml/encode-face", headers={"X-API-Key": "your-ml-service-api-key"}, json={
    "image_base64": b64,
    "validate_single": True,
    "min_face_area_ratio": 0.05,
    "num_jitters": 5
})
print(resp.json())
