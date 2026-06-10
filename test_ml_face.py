import httpx
import base64
import urllib.request

# Download a sample face image
urllib.request.urlretrieve("https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/obama.jpg", "obama.jpg")

with open("obama.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

resp = httpx.post("http://localhost:8001/api/ml/encode-face", headers={"X-API-Key": "your-ml-service-api-key"}, json={
    "image_base64": b64,
    "validate_single": True,
    "min_face_area_ratio": 0.05,
    "num_jitters": 5
})
print(resp.json())
