/**
 * FaceLivenessEnrollment.jsx
 * ===========================
 * Live-video face enrollment component for student profile page.
 *
 * Usage in StudentProfile.jsx:
 *   import FaceLivenessEnrollment from "./FaceLivenessEnrollment";
 *   <FaceLivenessEnrollment studentId={data.id} onSuccess={() => queryClient.invalidateQueries(["myStudentProfile"])} />
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Camera, RotateCcw, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { toast } from "react-hot-toast";

const ML_SERVICE_URL = import.meta.env.VITE_ML_SERVICE_URL || "http://localhost:8001";
const CAPTURE_INTERVAL_MS = 400;
const TARGET_FRAMES = 15;
const VIDEO_WIDTH = 480;
const VIDEO_HEIGHT = 360;

const GUIDANCE_STEPS = [
  { id: "front", label: "Hadap ke depan", emoji: "😊", durationMs: 2000 },
  { id: "right", label: "Putar kepala ke kanan", emoji: "➡️", durationMs: 2500 },
  { id: "left", label: "Putar kepala ke kiri", emoji: "⬅️", durationMs: 2500 },
  { id: "front_end", label: "Hadap depan lagi", emoji: "😊", durationMs: 2000 },
];

export default function FaceLivenessEnrollment({ studentId, onSuccess, token }) {
  const [phase, setPhase] = useState("idle");
  const [currentStep, setCurrentStep] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const framesRef = useRef([]);
  const captureRef = useRef(null);
  const stepTimerRef = useRef(null);

  const startWebcam = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setErrorMsg("Kamera tidak didukung atau Anda tidak berada di koneksi aman (HTTPS/localhost).");
      setPhase("error");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: VIDEO_WIDTH, height: VIDEO_HEIGHT, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      setPhase("preview");
    } catch (err) {
      console.error("Camera access error:", err);
      setErrorMsg("Tidak dapat mengakses kamera. Pastikan izin kamera diberikan.");
      setPhase("error");
    }
  }, []);

  const stopWebcam = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (captureRef.current) clearInterval(captureRef.current);
    if (stepTimerRef.current) clearTimeout(stepTimerRef.current);
  }, []);

  useEffect(() => () => stopWebcam(), [stopWebcam]);

  useEffect(() => {
    if ((phase === "preview" || phase === "capturing") && videoRef.current && streamRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current;
        videoRef.current.play().catch((err) => {
          console.error("Error playing video:", err);
        });
      }
    }
  }, [phase]);

  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;
    const ctx = canvas.getContext("2d");
    canvas.width = VIDEO_WIDTH;
    canvas.height = VIDEO_HEIGHT;
    ctx.drawImage(video, 0, 0, VIDEO_WIDTH, VIDEO_HEIGHT);
    framesRef.current.push(canvas.toDataURL("image/jpeg", 0.85));
    setFrameCount(framesRef.current.length);
  }, []);

  const uploadFrames = useCallback(async () => {
    stopWebcam();
    setPhase("uploading");
    const frames = framesRef.current;

    if (frames.length < 5) {
      setErrorMsg(`Hanya ${frames.length} frame berhasil diambil. Minimal 5 diperlukan.`);
      setPhase("error");
      return;
    }

    try {
      const resp = await fetch(`${ML_SERVICE_URL}/face/register-video`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": import.meta.env.VITE_ML_API_KEY || "your-ml-service-api-key",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ student_id: studentId, frames }),
      });
      const data = await resp.json();
      if (!resp.ok || !data.success) throw new Error(data.detail || data.message || "Registrasi gagal.");
      setPhase("done");
      toast.success(`Wajah berhasil didaftarkan (${data.frames_used} frame)!`);
      if (onSuccess) onSuccess();
    } catch (err) {
      setErrorMsg(err.message || "Terjadi kesalahan saat mengirim data.");
      setPhase("error");
    }
  }, [studentId, token, onSuccess, stopWebcam]);

  const startCapture = useCallback(() => {
    framesRef.current = [];
    setFrameCount(0);
    setCurrentStep(0);
    setPhase("capturing");

    captureRef.current = setInterval(() => {
      captureFrame();
      if (framesRef.current.length >= TARGET_FRAMES + 5) clearInterval(captureRef.current);
    }, CAPTURE_INTERVAL_MS);

    let stepIdx = 0;
    const advanceStep = () => {
      stepIdx++;
      if (stepIdx < GUIDANCE_STEPS.length) {
        setCurrentStep(stepIdx);
        stepTimerRef.current = setTimeout(advanceStep, GUIDANCE_STEPS[stepIdx].durationMs);
      } else {
        clearInterval(captureRef.current);
        uploadFrames();
      }
    };
    stepTimerRef.current = setTimeout(advanceStep, GUIDANCE_STEPS[0].durationMs);
  }, [captureFrame, uploadFrames]);

  const reset = useCallback(() => {
    stopWebcam();
    framesRef.current = [];
    setFrameCount(0);
    setCurrentStep(0);
    setPhase("idle");
    setErrorMsg("");
  }, [stopWebcam]);

  const progressPct = phase === "capturing"
    ? Math.min(100, (frameCount / TARGET_FRAMES) * 100)
    : phase === "done" ? 100 : 0;

  const currentGuidance = GUIDANCE_STEPS[currentStep] || GUIDANCE_STEPS[0];

  return (
    <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] shadow-sm p-6 space-y-4">
      <div>
        <h4 className="text-base font-bold text-[var(--text-main)]">Pendaftaran Wajah</h4>
        <p className="text-xs text-[var(--text-body)]/80 mt-1 max-w-md leading-relaxed">
          Daftarkan wajah Anda menggunakan video pendek untuk akurasi lebih tinggi.
          Ikuti panduan gerakan kepala selama proses berlangsung.
        </p>
      </div>

      {phase === "idle" && (
        <button
          onClick={startWebcam}
          className="flex items-center gap-2 px-5 py-2.5 bg-[var(--action-info-bg)] hover:bg-[var(--action-info-hover)] text-white text-sm font-semibold rounded-xl transition active:scale-95 shadow-sm"
        >
          <Camera size={18} />
          Mulai Pendaftaran Video
        </button>
      )}

      {(phase === "preview" || phase === "capturing") && (
        <div className="space-y-3">
          <div className="relative w-full max-w-sm rounded-xl overflow-hidden border-2 border-[var(--border-color)] bg-black mx-auto">
            <video
              ref={videoRef}
              className="w-full block"
              autoPlay
              playsInline
              muted
              style={{ transform: "scaleX(-1)" }}
            />
            {phase === "capturing" && (
              <div className="absolute inset-0 flex flex-col items-center justify-end pb-4 pointer-events-none">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="border-4 border-white/60 rounded-full" style={{ width: 180, height: 220 }} />
                </div>
                <div className="bg-black/70 backdrop-blur-sm text-white text-sm font-semibold px-4 py-2 rounded-full flex items-center gap-2 z-10">
                  <span className="text-lg">{currentGuidance.emoji}</span>
                  {currentGuidance.label}
                </div>
              </div>
            )}
            {phase === "preview" && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                <div className="border-4 border-white/60 rounded-full" style={{ width: 180, height: 220 }} />
              </div>
            )}
          </div>

          {phase === "capturing" && (
            <div className="max-w-sm mx-auto space-y-1">
              <div className="flex justify-between text-xs text-[var(--text-body)]/70">
                <span>Merekam… {frameCount} frame</span>
                <span>{Math.round(progressPct)}%</span>
              </div>
              <div className="h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--action-info-bg)] rounded-full transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <div className="flex justify-between mt-2">
                {GUIDANCE_STEPS.map((step, i) => (
                  <div key={step.id} className={`flex flex-col items-center gap-0.5 ${i <= currentStep ? "opacity-100" : "opacity-30"}`}>
                    <span className="text-base">{step.emoji}</span>
                    <span className="text-[9px] text-[var(--text-body)] text-center leading-tight" style={{ maxWidth: 56 }}>
                      {step.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2 max-w-sm mx-auto">
            {phase === "preview" && (
              <>
                <button
                  onClick={startCapture}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-[var(--action-info-bg)] hover:bg-[var(--action-info-hover)] text-white text-sm font-semibold rounded-xl transition active:scale-95"
                >
                  <Camera size={16} />
                  Mulai Rekam
                </button>
                <button
                  onClick={reset}
                  className="px-4 py-2.5 border border-[var(--border-color)] text-[var(--text-body)] text-sm rounded-xl hover:bg-[var(--bg-secondary)] transition"
                >
                  Batal
                </button>
              </>
            )}
            {phase === "capturing" && (
              <p className="text-xs text-[var(--text-body)]/60 text-center w-full">
                Ikuti petunjuk di atas. Perekaman akan selesai otomatis…
              </p>
            )}
          </div>
        </div>
      )}

      {phase === "uploading" && (
        <div className="flex flex-col items-center gap-3 py-6">
          <Loader2 className="animate-spin text-[var(--action-info-bg)]" size={32} />
          <p className="text-sm text-[var(--text-body)]">Memproses {frameCount} frame… Harap tunggu.</p>
        </div>
      )}

      {phase === "done" && (
        <div className="flex flex-col items-center gap-3 py-4">
          <CheckCircle className="text-[var(--success)]" size={40} />
          <p className="text-sm font-semibold text-[var(--text-main)]">Wajah berhasil didaftarkan!</p>
          <p className="text-xs text-[var(--text-body)]/70 text-center max-w-xs">
            Model wajah Anda telah diperbarui dari {frameCount} frame.
          </p>
          <button onClick={reset} className="mt-2 flex items-center gap-1.5 text-xs text-[var(--primary)] hover:underline">
            <RotateCcw size={12} />
            Daftar ulang
          </button>
        </div>
      )}

      {phase === "error" && (
        <div className="flex flex-col items-center gap-3 py-4">
          <XCircle className="text-[var(--danger)]" size={36} />
          <p className="text-sm font-semibold text-[var(--danger)]">Pendaftaran gagal</p>
          <p className="text-xs text-[var(--text-body)]/70 text-center max-w-xs">{errorMsg}</p>
          <button
            onClick={reset}
            className="mt-2 flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] text-sm rounded-xl transition hover:bg-[var(--bg-primary)]"
          >
            <RotateCcw size={14} />
            Coba lagi
          </button>
        </div>
      )}

      <canvas ref={canvasRef} className="hidden" />

      {phase === "idle" && (
        <div className="bg-[var(--bg-primary)] text-[var(--text-body)]/80 text-[10px] px-3 py-2 rounded-lg border border-[var(--border-color)] font-medium">
          💡 Tips: Pastikan pencahayaan baik, wajah terlihat jelas, dan tidak ada aksesori yang menutupi wajah.
        </div>
      )}
    </div>
  );
}