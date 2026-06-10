import React, { useState, useEffect } from "react";

export default function FaceOverlay({ faces, videoRef, mirrored = false }) {
  const [videoDimensions, setVideoDimensions] = useState(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (videoRef.current && videoRef.current.video && videoRef.current.video.videoWidth) {
        const videoEl = videoRef.current.video;
        setVideoDimensions(prev => {
          const newDims = {
            width: videoEl.videoWidth,
            height: videoEl.videoHeight,
            displayWidth: videoEl.clientWidth,
            displayHeight: videoEl.clientHeight
          };
          if (!prev || 
              prev.width !== newDims.width || 
              prev.height !== newDims.height || 
              prev.displayWidth !== newDims.displayWidth || 
              prev.displayHeight !== newDims.displayHeight) {
            return newDims;
          }
          return prev;
        });
      }
    };

    updateDimensions();

    const videoEl = videoRef.current?.video;
    if (videoEl) {
      videoEl.addEventListener("loadedmetadata", updateDimensions);
      videoEl.addEventListener("play", updateDimensions);
    }

    window.addEventListener("resize", updateDimensions);
    const interval = setInterval(updateDimensions, 500);

    return () => {
      if (videoEl) {
        videoEl.removeEventListener("loadedmetadata", updateDimensions);
        videoEl.removeEventListener("play", updateDimensions);
      }
      window.removeEventListener("resize", updateDimensions);
      clearInterval(interval);
    };
  }, [videoRef, faces]); 
  
  const { width: videoWidth, height: videoHeight, displayWidth, displayHeight } = videoDimensions || {};

  if (!videoWidth) return null;

  // Assuming object-contain:
  // Calculate the actual rendered video size (letterboxed/pillarboxed)
  const videoAspect = videoWidth / videoHeight;
  const containerAspect = displayWidth / displayHeight;
  
  let renderWidth, renderHeight, offsetX, offsetY;

  if (containerAspect > videoAspect) {
     // Container is wider than video (black bars left/right)
     renderHeight = displayHeight;
     renderWidth = renderHeight * videoAspect;
     offsetY = 0;
     offsetX = (displayWidth - renderWidth) / 2;
  } else {
     // Container is taller than video (black bars top/bottom)
     renderWidth = displayWidth;
     renderHeight = displayWidth / videoAspect;
     offsetX = 0;
     offsetY = (displayHeight - renderHeight) / 2;
  }
  
  return (
    <div
      className="absolute inset-0 pointer-events-none"
      style={{ width: displayWidth, height: displayHeight }}
    >
      {faces.map((f, idx) => {
        const { top, right, bottom, left } = f.box;

        const boxWidth = (right - left) * renderWidth;
        const boxHeight = (bottom - top) * renderHeight;

        let x;
        if (mirrored) {
          x = offsetX + (1 - right) * renderWidth;
        } else {
          x = offsetX + left * renderWidth;
        }

        const y = offsetY + top * renderHeight;
        
        const color =
          f.status === "present"
            ? "var(--success)"
            : f.status === "uncertain"
            ? "var(--warning)"
            : f.status === "spoof"
            ? "var(--danger)"
            : "#3b82f6"; // Vibrant blue for unknown/scanning face

        const label =
          f.status === "present"
            ? `${f.student?.name} (${Math.round(f.confidence * 100)}%)`
            : f.status === "uncertain"
            ? `${f.student?.name || "Uncertain"} (${Math.round((f.confidence || 0) * 100)}%?)`
            : f.status === "spoof"
            ? "FAKE/SPOOF"
            : "Face Detected (Scanning...)";

        return (
          <div
            key={idx}
            style={{
              position: "absolute",
              left: `${x}px`,
              top: `${y}px`,
              width: `${boxWidth}px`,
              height: `${boxHeight}px`,
              border: `2px solid ${color}`,
              borderRadius: "8px",
              background: `${color}20`,
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "-18px",
                left: 0,
                background: color,
                color: "var(--text-on-primary)",
                fontSize: "10px",
                padding: "2px 6px",
                borderRadius: "4px",
                whiteSpace: "nowrap",
                fontWeight: 600,
              }}
            >
              {label}
            </div>
          </div>
        );
      })}
    </div>
  );
}
