import { useRef, useState, useEffect, useCallback } from 'react';
import { Camera, X, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from './Button';

const MAX_CAPTURES = 10;

/**
 * WebcamCapture — live webcam preview with snapshot functionality.
 *
 * Props:
 *   onCapture(blobs: Blob[])  — called every time the captured set changes
 *   maxCaptures (number)      — cap on captures (default 10)
 */
export const WebcamCapture = ({ onCapture, maxCaptures = MAX_CAPTURES }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);
  const [captures, setCaptures] = useState([]); // [{ blob, url }]
  const [isCapturing, setIsCapturing] = useState(false);

  // ── Start webcam stream ──────────────────────────────────────────────────
  const startStream = useCallback(async () => {
    setError(null);
    setIsReady(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => setIsReady(true);
      }
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Camera access was denied. Please allow camera permission and try again.');
      } else if (err.name === 'NotFoundError') {
        setError('No camera device found. Please connect a webcam.');
      } else {
        setError(`Camera error: ${err.message}`);
      }
    }
  }, []);

  // ── Stop webcam stream ───────────────────────────────────────────────────
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setIsReady(false);
  }, []);

  // Start on mount, stop on unmount
  useEffect(() => {
    startStream();
    return () => stopStream();
  }, [startStream, stopStream]);

  // Notify parent whenever captures change
  useEffect(() => {
    onCapture(captures.map((c) => c.blob));
  }, [captures, onCapture]);

  // Revoke object URLs on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      captures.forEach((c) => URL.revokeObjectURL(c.url));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Capture a frame ──────────────────────────────────────────────────────
  const handleCapture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isReady) return;
    if (captures.length >= maxCaptures) return;

    setIsCapturing(true);
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          setCaptures((prev) => [...prev, { blob, url }]);
        }
        setIsCapturing(false);
      },
      'image/jpeg',
      0.92
    );
  }, [isReady, captures.length, maxCaptures]);

  // ── Remove a captured frame ──────────────────────────────────────────────
  const handleRemove = useCallback((index) => {
    setCaptures((prev) => {
      URL.revokeObjectURL(prev[index].url);
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  const canCapture = isReady && captures.length < maxCaptures;

  return (
    <div className="space-y-4">
      {/* Video preview */}
      <div className="relative rounded-lg overflow-hidden bg-black aspect-video w-full">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover transition-opacity duration-300 ${isReady ? 'opacity-100' : 'opacity-0'}`}
        />

        {/* Loading state */}
        {!isReady && !error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white/70 gap-2">
            <Camera className="h-8 w-8 animate-pulse" />
            <span className="text-sm">Starting camera…</span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white gap-3 p-4">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-sm text-center text-white/80">{error}</p>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="text-white border-white/40 hover:bg-white/10"
              onClick={startStream}
            >
              <RefreshCw className="h-3 w-3 mr-2" />
              Retry
            </Button>
          </div>
        )}

        {/* Live indicator */}
        {isReady && (
          <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/50 rounded-full px-2 py-0.5">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-white text-xs font-medium">LIVE</span>
          </div>
        )}

        {/* Capture count badge */}
        {isReady && (
          <div className="absolute top-2 right-2 bg-black/50 rounded-full px-2 py-0.5">
            <span className="text-white text-xs font-medium">
              {captures.length} / {maxCaptures}
            </span>
          </div>
        )}
      </div>

      {/* Hidden canvas used for frame capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Capture button */}
      <Button
        type="button"
        className="w-full"
        onClick={handleCapture}
        disabled={!canCapture || isCapturing}
        id="webcam-capture-btn"
      >
        <Camera className="mr-2 h-4 w-4" />
        {captures.length >= maxCaptures
          ? `Max ${maxCaptures} captures reached`
          : isCapturing
          ? 'Capturing…'
          : 'Capture Photo'}
      </Button>

      {/* Thumbnail grid */}
      {captures.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-2 font-medium">
            Captured ({captures.length}) — click × to remove
          </p>
          <div className="grid grid-cols-5 gap-2">
            {captures.map((capture, i) => (
              <div key={i} className="relative group rounded-md overflow-hidden aspect-square bg-muted">
                <img
                  src={capture.url}
                  alt={`Capture ${i + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => handleRemove(i)}
                  className="absolute top-0.5 right-0.5 bg-black/70 hover:bg-red-600 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={`Remove capture ${i + 1}`}
                >
                  <X className="h-3 w-3 text-white" />
                </button>
                <span className="absolute bottom-0.5 left-0.5 text-[10px] text-white bg-black/50 rounded px-1">
                  {i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
