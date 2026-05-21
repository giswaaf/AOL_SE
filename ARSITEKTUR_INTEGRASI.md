# 🎓 FaceAttend — Sistem Absensi Wajah Terintegrasi
## Arsitektur Integrasi 3 Repository

---

## 📦 Sumber Komponen

| Komponen | Repo | Fungsi |
|---|---|---|
| **Face Recognition** | `ageitgey/face_recognition` | Encode & match wajah (dlib, 99.38% akurasi) |
| **Smart Attendance** | `nem-web/smart-attendance` | Web app fullstack (FastAPI + React + MongoDB) |
| **Anti-Spoofing** | `minivision-ai/Silent-Face-Anti-Spoofing` | Deteksi wajah palsu (foto/layar/topeng) |

---

## 🏗️ Arsitektur Sistem

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                       │
│  nem-web/smart-attendance → /frontend                        │
│  - Dashboard Guru & Siswa                                    │
│  - Webcam component (React Webcam)                          │
│  - Halaman Mark Attendance (dimodifikasi)                    │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼─────────────────────────────────────┐
│                   BACKEND API (FastAPI :8000)                 │
│  nem-web/smart-attendance → /server/backend-api              │
│  - Auth, Student, Attendance routes                          │
│  - MongoDB (data absensi, profil siswa)                      │
│  - Cloudinary (foto profil)                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │ Internal HTTP
┌────────────────────────▼─────────────────────────────────────┐
│                   ML SERVICE (FastAPI :8001)                  │
│  ← DIMODIFIKASI: Gabungan 3 repo ←                          │
│                                                              │
│  Step 1: Anti-Spoofing Check                                 │
│  minivision-ai/Silent-Face-Anti-Spoofing                    │
│  └─ Pastikan wajah = nyata (bukan foto/layar)               │
│                                                              │
│  Step 2: Face Detection & Encoding                           │
│  ageitgey/face_recognition                                   │
│  └─ Encode wajah → 128-dim vector                           │
│                                                              │
│  Step 3: Face Matching                                       │
│  ageitgey/face_recognition + nem-web ML                     │
│  └─ Bandingkan dengan database encoding siswa               │
│                                                              │
│  Step 4: Return Result                                       │
│  └─ student_id, nama, confidence, is_real                   │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    DATABASE (MongoDB)                         │
│  - students: { _id, name, face_encoding[], photo_url }      │
│  - attendance: { student_id, subject, time_in, time_out }   │
│  - subjects, users (teachers)                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Alur Kerja Absensi

```
Siswa berdiri di depan kamera
        │
        ▼
[1] Kamera capture frame
        │
        ▼
[2] ANTI-SPOOFING (Silent-Face-Anti-Spoofing)
    ├── PALSU → Tolak, tampilkan peringatan
    └── NYATA → lanjut...
        │
        ▼
[3] FACE DETECTION (face_recognition)
    ├── Tidak ada wajah → Minta siswa mendekat
    └── Wajah ditemukan → encode ke 128-dim vector
        │
        ▼
[4] FACE MATCHING (face_recognition.compare_faces)
    ├── Unknown → "Wajah tidak dikenali"
    └── Match → student_id, confidence
        │
        ▼
[5] CATAT ABSENSI (Backend API → MongoDB)
    ├── time_in (awal kelas) ATAU time_out (akhir kelas)
    └── Konfirmasi ke siswa di layar
```

---

## 📁 Struktur Direktori Proyek

```
faceattend/
├── frontend/                    ← dari nem-web/smart-attendance
│   └── src/
│       ├── pages/
│       │   └── MarkAttendance.jsx  ← DIMODIFIKASI (tambah anti-spoofing feedback)
│       └── ...
│
├── server/
│   ├── backend-api/             ← dari nem-web/smart-attendance
│   │   └── app/
│   │       ├── api/routes/attendance.py  ← DIMODIFIKASI
│   │       └── ...
│   │
│   └── ml-service/              ← DIROMBAK TOTAL (inti integrasi)
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   │   └── config.py
│       │   ├── ml/
│       │   │   ├── anti_spoofing.py     ← dari Silent-Face-Anti-Spoofing
│       │   │   ├── face_recognizer.py   ← dari ageitgey/face_recognition
│       │   │   └── attendance_pipeline.py  ← PIPELINE UTAMA (integrasi)
│       │   ├── api/routes/
│       │   │   └── face.py              ← endpoint diperbarui
│       │   └── schemas/
│       │       └── face.py
│       ├── resources/
│       │   └── anti_spoof_models/       ← model dari Silent-Face-Anti-Spoofing
│       └── requirements.txt             ← gabungan dependencies
│
└── docker-compose.yml           ← dari nem-web/smart-attendance (dimodifikasi)
```

---

## ⚙️ File Kunci yang Diintegrasikan

### 1. `ml-service/app/ml/anti_spoofing.py`
Wrapper untuk `minivision-ai/Silent-Face-Anti-Spoofing`:
- Input: frame gambar (numpy array)
- Output: `{"is_real": bool, "confidence": float, "label": str}`

### 2. `ml-service/app/ml/face_recognizer.py`
Wrapper untuk `ageitgey/face_recognition`:
- `encode_face(image)` → 128-dim vector
- `match_face(encoding, known_encodings)` → student_id + confidence

### 3. `ml-service/app/ml/attendance_pipeline.py`
**INTI INTEGRASI** — menggabungkan keduanya:
```
verify_attendance(image_bytes, known_encodings_db)
  1. anti_spoofing.check(image)      → is_real
  2. face_recognizer.encode(image)   → encoding
  3. face_recognizer.match(encoding) → student_id
  4. return AttendanceResult
```

### 4. `ml-service/requirements.txt` (gabungan)
```
face_recognition>=1.3.0
dlib>=19.22.0
opencv-python-headless>=4.5.0
torch>=1.7.0           # untuk Silent-Face-Anti-Spoofing
torchvision>=0.8.0
numpy>=1.21.0
Pillow>=8.0.0
fastapi>=0.115.5
uvicorn>=0.32.1
```

---

## 🔌 API Endpoint ML Service (Diperbarui)

### `POST /face/verify-attendance`
Endpoint utama untuk absensi masuk/keluar.

**Request:**
```json
{
  "image": "base64_encoded_image_string",
  "subject_id": "string",
  "session_type": "check_in" | "check_out"
}
```

**Response:**
```json
{
  "success": true,
  "is_real_face": true,
  "spoofing_confidence": 0.97,
  "student_id": "507f1f77bcf86cd799439011",
  "student_name": "Budi Santoso",
  "recognition_confidence": 0.95,
  "session_type": "check_in",
  "timestamp": "2026-05-19T08:00:00"
}
```

### `POST /face/register`
Daftarkan wajah siswa baru ke database encoding.

**Request:** `multipart/form-data` dengan `student_id` + `image`

---

## 🚀 Langkah Setup & Instalasi

### 1. Clone semua repo
```bash
# Clone smart-attendance sebagai base
git clone https://github.com/nem-web/smart-attendance.git faceattend
cd faceattend

# Clone anti-spoofing (salin folder resources & src ke ml-service)
git clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing.git /tmp/anti-spoof
cp -r /tmp/anti-spoof/resources server/ml-service/
cp -r /tmp/anti-spoof/src server/ml-service/app/anti_spoof_src/
```

### 2. Install dependencies ML Service
```bash
# Ubuntu/Debian: Install dlib prerequisites
sudo apt-get install -y cmake libboost-all-dev

cd server/ml-service
pip install -r requirements.txt
```

### 3. Download model Anti-Spoofing
Model sudah ada di `resources/anti_spoof_models/` setelah clone repo.

### 4. Jalankan semua service
```bash
# Terminal 1: MongoDB
mongod

# Terminal 2: Backend API
cd server/backend-api && uvicorn app.main:app --port 8000 --reload

# Terminal 3: ML Service (yang sudah diintegrasikan)
cd server/ml-service && uvicorn app.main:app --port 8001 --reload

# Terminal 4: Frontend
cd frontend && npm run dev
```

---

## ⚠️ Catatan Teknis Penting

### Kompatibilitas dlib + PyTorch
`face_recognition` menggunakan dlib, sementara Silent-Face-Anti-Spoofing menggunakan PyTorch. Keduanya bisa berjalan di environment yang sama, namun install dlib terlebih dahulu sebelum torch untuk menghindari konflik.

### Mode Check-In vs Check-Out
Backend API perlu dimodifikasi untuk mendukung 2 sesi per kelas:
- `check_in`: saat awal kelas (wajib face recognition)
- `check_out`: saat akhir kelas (face recognition untuk konfirmasi)

### Akurasi Anti-Spoofing
Model yang disediakan (80x80 input) memiliki TPR 97.8% pada FPR 1e-5. Untuk lingkungan produksi, pastikan:
- Pencahayaan ruangan cukup
- Kamera minimal 720p
- Jarak optimal 50-100cm dari kamera

### Penyimpanan Face Encoding
Face encoding (128-dim vector) disimpan di MongoDB per siswa, bukan gambar aslinya. Ini lebih efisien dan menjaga privasi.

---

## 📊 Perbandingan Sebelum vs Sesudah Integrasi

| Aspek | smart-attendance (asli) | FaceAttend (terintegrasi) |
|---|---|---|
| Face Engine | MediaPipe (basic) | dlib via face_recognition (99.38%) |
| Anti-Spoofing | ❌ Tidak ada | ✅ MiniFASNet (97.8% TPR) |
| Check-Out | ❌ Tidak ada | ✅ Ada (konfirmasi akhir kelas) |
| Keamanan | Bisa ditipu foto | Wajah nyata wajib |
| Akurasi | ~90% | ~99% |
