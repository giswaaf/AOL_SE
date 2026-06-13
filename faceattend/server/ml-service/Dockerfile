FROM python:3.10-slim

# ✅ Required runtime libs for OpenCV & MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    cmake \
    build-essential \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download models saat build
RUN mkdir -p /app/app/ml && \
    curl -L "https://storage.googleapis.com/mediapipe-assets/blaze_face_short_range.tflite" \
    -o /app/app/ml/blaze_face_short_range.tflite && \
    curl -L "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" \
    -o /app/app/ml/face_landmarker.task

COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8001

# Use entrypoint to download models at runtime if needed
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
