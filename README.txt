========================================================================
                               FACEATTEND
                     Sistem Absensi Face Recognition
             Panduan Lengkap Instalasi & Menjalankan Aplikasi
========================================================================

1. GAMBARAN UMUM SISTEM
------------------------------------------------------------------------
FaceAttend adalah sistem absensi otomatis berbasis pengenalan wajah yang 
mengintegrasikan tiga komponen utama:
- face_recognition (ageitgey) - Engine pengenalan wajah akurasi 99.38%
- Silent-Face-Anti-Spoofing (minivision-ai) - Deteksi wajah palsu 
  (foto/layar/topeng)
- Smart Attendance (nem-web) - Web app fullstack dengan dashboard guru 
  & siswa

Sistem terdiri dari 3 service yang berjalan bersamaan:

+-------------------+--------+------------------------+
| Service           | Port   | URL                    |
+-------------------+--------+------------------------+
| MongoDB           | 27017  | localhost:27017        |
| Backend API       | 8000   | http://localhost:8000  |
| ML Service        | 8001   | http://localhost:8001  |
| Frontend          | 5173   | http://localhost:5173  |
+-------------------+--------+------------------------+


2. PRASYARAT - INSTALL DULU
------------------------------------------------------------------------
Pastikan semua software berikut sudah terinstall sebelum memulai:

- MongoDB Community (v7.0+) -> Database
  Link: https://www.mongodb.com/try/download/community
- Python (v3.10+) -> Backend & ML
  Link: https://www.python.org/downloads
- Node.js (v18+ LTS) -> Frontend
  Link: https://nodejs.org/en/download
- Git (Latest) -> Clone repo
  Link: https://git-scm.com/download/win
- Anaconda / Miniconda (Latest) -> Python env (dlib)
  Link: https://docs.anaconda.com/miniconda

PERINGATAN: Semua software di atas wajib diinstall terlebih dahulu. 
Jangan lewati langkah ini.


3. STRUKTUR FOLDER PROJECT
------------------------------------------------------------------------
[PROJECT_ROOT]/
├── attendance_pipeline.py
├── face_route.py
├── requirements_ml_service.txt
└── faceattend/                  <- folder utama project
    ├── frontend/                <- React app
    └── server/
        ├── backend-api/         <- FastAPI backend
        └── ml-service/          <- ML + face recognition
            └── app/
                ├── ml/
                │   └── attendance_pipeline.py
                └── api/routes/
                    └── face.py


4. LANGKAH SETUP (SEKALI SAJA)
------------------------------------------------------------------------
INFO: Langkah setup ini hanya perlu dilakukan sekali. Setelah selesai, 
cukup ikuti bagian 5 untuk menjalankan aplikasi setiap hari.

4.1 Clone Repository
Buka Command Prompt atau PowerShell, lalu jalankan:
  cd [PROJECT_ROOT]
  git clone https://github.com/nem-web/smart-attendance.git faceattend
  cd faceattend

Clone anti-spoofing dan copy file yang diperlukan:
  git clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing.git C:\temp\silent-face
  xcopy /E /I C:\temp\silent-face\resources server\ml-service\resources
  xcopy /E /I C:\temp\silent-face\src server\ml-service\app\anti_spoof_src

Copy file integrasi:
  mkdir server\ml-service\app\ml
  copy ..\attendance_pipeline.py server\ml-service\app\ml\attendance_pipeline.py
  copy ..\face_route.py server\ml-service\app\api\routes\face.py
  copy ..\requirements_ml_service.txt server\ml-service\requirements.txt

4.2 Setup Backend API
  cd server\backend-api
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt

Buat file konfigurasi .env:
  copy .env.example .env
  notepad .env

Isi file .env dengan nilai berikut (minimal):
  MONGO_URI=mongodb://localhost:27017
  MONGO_DB=smart_attendance
  JWT_SECRET=<generate dengan: python -c "import secrets; print(secrets.token_urlsafe(32))">
  SESSION_SECRET_KEY=<generate lagi dengan perintah yang sama>

4.3 Setup ML Service
PERINGATAN: Gunakan Anaconda Prompt untuk langkah ini, bukan PowerShell biasa.

  conda create -n faceattend python=3.10
  conda activate faceattend
  conda install -c conda-forge dlib
  cd [PROJECT_ROOT]\faceattend\server\ml-service
  pip install -r requirements.txt
  pip install mediapipe==0.10.9

Download model yang diperlukan:
  python download_models.py

Buat file .env ML Service:
  echo ML_SERVICE_HOST=0.0.0.0 > .env
  echo ML_SERVICE_PORT=8001 >> .env
  echo BACKEND_API_URL=http://localhost:8000 >> .env

4.4 Setup Frontend
  cd [PROJECT_ROOT]\faceattend\frontend
  npm install
  echo VITE_API_URL=http://localhost:8000 > .env


5. CARA MENJALANKAN APLIKASI
------------------------------------------------------------------------
INFO: Buka 4 terminal/jendela terpisah. Setiap service harus berjalan 
bersamaan.

Terminal 1 — MongoDB
Jika MongoDB sudah diinstall sebagai Windows Service (centang saat 
instalasi), MongoDB otomatis berjalan. Cukup verifikasi:
  net start MongoDB
Jika belum sebagai service, jalankan manual:
  mongod

Terminal 2 — Backend API
  cd [PROJECT_ROOT]\faceattend\server\backend-api
  .venv\Scripts\activate
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
*Tanda berhasil:* muncul "Application startup complete." di terminal.

Terminal 3 — ML Service
PERINGATAN: Gunakan Anaconda Prompt untuk terminal ini.
  conda activate faceattend
  cd [PROJECT_ROOT]\faceattend\server\ml-service
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
*Tanda berhasil:* muncul "Application startup complete." di terminal.

Terminal 4 — Frontend
  cd [PROJECT_ROOT]\faceattend\frontend
  npm run dev
*Tanda berhasil:* muncul "Local: http://localhost:5173/" di terminal.

INFO: Buka browser dan akses http://localhost:5173 untuk menggunakan aplikasi.

Urutan Mematikan Aplikasi:
Tekan Ctrl+C di setiap terminal dengan urutan berikut:
1. Frontend (Terminal 4)
2. ML Service (Terminal 3)
3. Backend API (Terminal 2)
4. MongoDB terakhir (Terminal 1)


6. TROUBLESHOOTING
------------------------------------------------------------------------
- MongoDB: WinError 10061 — connection refused
  MongoDB belum berjalan. Jalankan: `net start MongoDB`
  Atau install MongoDB Community dan centang "Install as Service".

- dlib: Failed building wheel
  Gunakan conda untuk install dlib: `conda install -c conda-forge dlib`

- ModuleNotFoundError: No module named 'xxx'
  Install module yang kurang: `pip install nama-module`

- mediapipe: module has no attribute 'solutions'
  Install versi mediapipe yang kompatibel: `pip install mediapipe==0.10.9`

- npm: tidak dikenali di PowerShell
  Aktifkan execution policy PowerShell:
  `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

- FileNotFoundError: blaze_face_short_range.tflite
  Download model yang kurang: `python download_models.py`


7. URL AKSES APLIKASI
------------------------------------------------------------------------
+---------------------+--------+----------------------------+
| Komponen            | Port   | URL                        |
+---------------------+--------+----------------------------+
| Aplikasi Utama      | 5173   | http://localhost:5173      |
| API Docs Backend    | 8000   | http://localhost:8000/docs |
| API Docs ML Service | 8001   | http://localhost:8001/docs |
| MongoDB             | 27017  | localhost:27017            |
+---------------------+--------+----------------------------+

Demo Login (Testing):
  Guru:   teacher@gmail.com  /  teacher123
  Siswa:  student@gmail.com  /  student123

------------------------------------------------------------------------
FaceAttend — Dibuat dengan mengintegrasikan face_recognition + 
Silent-Face-Anti-Spoofing + Smart Attendance
