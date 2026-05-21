#!/bin/bash
# =============================================================
# setup_faceattend.sh
# Script otomatis untuk mengintegrasikan 3 repository menjadi
# satu sistem FaceAttend.
#
# Jalankan: bash setup_faceattend.sh
# =============================================================

set -e  # Hentikan jika ada error

echo "🎓 FaceAttend Setup Script"
echo "================================="

# ── 1. Clone smart-attendance sebagai base ─────────────────
echo ""
echo "📥 [1/5] Clone smart-attendance (base project)..."
git clone https://github.com/nem-web/smart-attendance.git faceattend
cd faceattend

# ── 2. Clone Silent-Face-Anti-Spoofing ────────────────────
echo ""
echo "📥 [2/5] Clone Silent-Face-Anti-Spoofing..."
git clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing.git /tmp/silent-face

# Copy model dan source ke ml-service
echo "   → Menyalin resources model..."
cp -r /tmp/silent-face/resources server/ml-service/
echo "   → Menyalin source code anti-spoofing..."
mkdir -p server/ml-service/app/anti_spoof_src
cp /tmp/silent-face/src/*.py server/ml-service/app/anti_spoof_src/
rm -rf /tmp/silent-face
echo "   ✅ Anti-spoofing siap."

# ── 3. Copy file integrasi ─────────────────────────────────
echo ""
echo "📋 [3/5] Menyalin file integrasi..."

# Buat direktori ml/ jika belum ada
mkdir -p server/ml-service/app/ml

# Salin file integrasi (asumsikan ada di direktori yang sama)
# Jika file ada di tempat lain, sesuaikan path-nya
cp ../attendance_pipeline.py server/ml-service/app/ml/attendance_pipeline.py 2>/dev/null || \
    echo "   ⚠️  attendance_pipeline.py tidak ditemukan, salin manual dari output."

cp ../face_route.py server/ml-service/app/api/routes/face.py 2>/dev/null || \
    echo "   ⚠️  face_route.py tidak ditemukan, salin manual dari output."

cp ../requirements_ml_service.txt server/ml-service/requirements.txt
echo "   ✅ File integrasi disalin."

# ── 4. Install system dependencies ────────────────────────
echo ""
echo "🔧 [4/5] Install system dependencies..."

# Deteksi OS
if [ -f /etc/debian_version ]; then
    echo "   Terdeteksi: Ubuntu/Debian"
    sudo apt-get update -q
    sudo apt-get install -y cmake libboost-all-dev python3-dev build-essential
elif [ "$(uname)" = "Darwin" ]; then
    echo "   Terdeteksi: macOS"
    brew install cmake boost
fi

# ── 5. Install Python dependencies ────────────────────────
echo ""
echo "🐍 [5/5] Install Python dependencies ML Service..."
cd server/ml-service
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip -q
echo "   → Install dlib (bisa memakan waktu 5-10 menit)..."
pip install dlib -q
echo "   → Install semua dependencies..."
pip install -r requirements.txt -q

echo ""
echo "================================="
echo "✅ Setup FaceAttend selesai!"
echo ""
echo "📋 Langkah selanjutnya:"
echo "   1. Copy .env.example → .env dan isi konfigurasi"
echo "   2. Jalankan MongoDB"
echo "   3. cd server/backend-api && uvicorn app.main:app --port 8000 --reload"
echo "   4. cd server/ml-service  && uvicorn app.main:app --port 8001 --reload"
echo "   5. cd frontend && npm install && npm run dev"
echo ""
echo "🌐 Akses: http://localhost:5173"
echo "📊 API Docs: http://localhost:8001/docs"
