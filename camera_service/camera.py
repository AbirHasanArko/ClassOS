import cv2
import threading
import time
import numpy as np
import subprocess
from typing import Optional, List

from backend.config import settings


class CameraManager:
    """Manages a single camera via OpenCV's VideoCapture.

    Runs a background thread that continuously grabs frames into a buffer.
    Consumers call ``get_latest_frame()`` to read the most recent capture.

    Multiple instances can be created for different physical cameras
    (e.g., Camera 0 for face recognition, Camera 1 for head counting).
    """

    def __init__(
        self,
        device_index: int,
        width: int = None,
        height: int = None,
        fps: int = None,
        fallback_indices: Optional[List[int]] = None,
    ):
        """
        Args:
            device_index:     Preferred /dev/videoN index to try first.
            fallback_indices: Additional indices to probe (in order) when
                              the preferred device is unavailable. The first
                              one that opens successfully is used.
                              Defaults to settings.CAMERA_USB_FALLBACK_INDICES.
        """
        self.device_index = device_index
        self.width = width or settings.CAMERA_RESOLUTION_WIDTH
        self.height = height or settings.CAMERA_RESOLUTION_HEIGHT
        self.fps = fps or settings.CAMERA_FPS

        # Build the probe order: preferred device first, then fallbacks.
        # Deduplicate while preserving order so the preferred index is
        # never tried twice even if it appears in fallback_indices.
        if fallback_indices is None:
            fallback_indices = settings.CAMERA_USB_FALLBACK_INDICES
        seen = set()
        self._probe_order: List[int] = []
        for idx in [device_index] + list(fallback_indices):
            if idx not in seen:
                seen.add(idx)
                self._probe_order.append(idx)

        self.cap: Optional[cv2.VideoCapture] = None
        self.active_device_index: Optional[int] = None  # Set after successful open

        # Buffer for the latest frame
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()

        self._running = False
        self._thread = None

    def _try_open(self, index: int) -> bool:
        """Attempt to open a VideoCapture at *index*. Returns True on success."""
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release()
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap = cap
        self.active_device_index = index
        return True

    def start(self):
        """Start the camera and the background frame-grabbing thread.

        Probes ``device_index`` first, then each entry in ``fallback_indices``
        until a camera opens successfully. Raises RuntimeError if none open.
        """
        if self._running:
            return

        # Start host systemd service via DBus
        try:
            svc_idx = '0' if self.device_index == 42 else '1'
            print(f"Starting host camera bridge service {svc_idx} via DBus...")
            subprocess.run([
                "dbus-send", "--system", "--print-reply", 
                "--dest=org.freedesktop.systemd1", "/org/freedesktop/systemd1", 
                "org.freedesktop.systemd1.Manager.StartUnit", 
                f"string:classos-camera-bridge-{svc_idx}.service", "string:replace"
            ], check=True, capture_output=True)
            # Give the bridge a moment to spin up and create the v4l2 device
            time.sleep(1.5)
        except Exception as e:
            print(f"Failed to start host bridge via DBus: {e}")

        opened = False
        for idx in self._probe_order:
            print(f"Trying camera device index {idx}...")
            if self._try_open(idx):
                if idx == self.device_index:
                    print(f"✅ Camera opened on preferred device /dev/video{idx}")
                else:
                    print(
                        f"⚠️  Preferred camera /dev/video{self.device_index} unavailable. "
                        f"Fell back to /dev/video{idx} (USB webcam)."
                    )
                opened = True
                break

        if not opened:
            tried = ", ".join(f"/dev/video{i}" for i in self._probe_order)
            raise RuntimeError(
                f"Could not open any camera. Tried: {tried}. "
                "Check that a camera is connected and not in use by another process."
            )

        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def start_if_available(self) -> bool:
        """
        Try to start the camera. Returns True on success, False if unavailable.
        Does NOT raise — safe for optional hardware (e.g. Camera 1).
        """
        if self._running:
            return True
        try:
            self.start()
            return True
        except RuntimeError as e:
            print(f"⚠️  Camera {self.device_index} unavailable: {e}")
            return False

    def _update_loop(self):
        """Daemon thread loop that constantly updates the latest frame buffer."""
        while self._running:
            ret, frame = self.cap.read()
            if ret:
                with self._lock:
                    self._latest_frame = frame

            # Yield slightly to prevent 100% CPU lock
            time.sleep(1.0 / self.fps)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return a copy of the latest captured frame."""
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
        return None

    def stop(self):
        """Stop the camera and release resources."""
        if not self._running:
            return

        print(f"Stopping camera service (active device /dev/video{self.active_device_index})...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None
        self.active_device_index = None

        # Stop host systemd service via DBus
        try:
            svc_idx = '0' if self.device_index == 42 else '1'
            print(f"Stopping host camera bridge service {svc_idx} via DBus...")
            subprocess.run([
                "dbus-send", "--system", "--print-reply", 
                "--dest=org.freedesktop.systemd1", "/org/freedesktop/systemd1", 
                "org.freedesktop.systemd1.Manager.StopUnit", 
                f"string:classos-camera-bridge-{svc_idx}.service", "string:replace"
            ], check=True, capture_output=True)
        except Exception as e:
            print(f"Failed to stop host bridge via DBus: {e}")


# ----- Singleton Instances -----

# Camera 0 — Entry camera for face recognition during Take Attendance mode.
# Preferred device: CAM/DISP 0 on Raspberry Pi 5 → /dev/video0
# Fallback: indices from CAMERA_0_USB_FALLBACK_INDICES (or shared CAMERA_USB_FALLBACK_INDICES)
camera_0 = CameraManager(
    device_index=settings.CAMERA_DEVICE_INDEX,
    fallback_indices=settings.camera_0_fallback_indices,
)

# Camera 1 — Classroom overhead camera for head counting only.
# Preferred device: CAM/DISP 1 on Raspberry Pi 5 → /dev/video2
# Fallback: indices from CAMERA_1_USB_FALLBACK_INDICES (or shared CAMERA_USB_FALLBACK_INDICES)
# This camera is optional; system falls back gracefully if unavailable.
camera_1 = CameraManager(
    device_index=settings.CAMERA_1_DEVICE_INDEX,
    fallback_indices=settings.camera_1_fallback_indices,
)

# Backward-compatible alias — camera_0 is the "primary" camera.
# Existing code that imports `from camera_service.camera import camera`
# continues to work without any changes.
camera = camera_0
