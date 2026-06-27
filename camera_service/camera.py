import cv2
import threading
import time
import numpy as np
from typing import Optional

from backend.config import settings


class CameraManager:
    """Manages a single camera via OpenCV's VideoCapture.

    Runs a background thread that continuously grabs frames into a buffer.
    Consumers call ``get_latest_frame()`` to read the most recent capture.

    Multiple instances can be created for different physical cameras
    (e.g., Camera 0 for face recognition, Camera 1 for head counting).
    """

    def __init__(self, device_index: int, width: int = None, height: int = None, fps: int = None):
        self.device_index = device_index
        self.width = width or settings.CAMERA_RESOLUTION_WIDTH
        self.height = height or settings.CAMERA_RESOLUTION_HEIGHT
        self.fps = fps or settings.CAMERA_FPS

        self.cap: Optional[cv2.VideoCapture] = None

        # Buffer for the latest frame
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()

        self._running = False
        self._thread = None

    def start(self):
        """Start the camera and the background frame-grabbing thread."""
        if self._running:
            return

        print(f"Starting camera service (device index {self.device_index})...")
        self.cap = cv2.VideoCapture(self.device_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera at device index {self.device_index}. "
                "Check that the camera is connected and not in use by another process."
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

        print(f"Stopping camera service (device index {self.device_index})...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None


# ----- Singleton Instances -----

# Camera 0 — Entry camera for face recognition during Take Attendance mode.
# Also used as the source for live face enrollment from the Pi's camera.
# Connected to CAM/DISP 0 connector on Raspberry Pi 5 → /dev/video0
camera_0 = CameraManager(device_index=settings.CAMERA_DEVICE_INDEX)

# Camera 1 — Classroom overhead camera for head counting only.
# Connected to CAM/DISP 1 connector on Raspberry Pi 5 → /dev/video2
# This camera is optional; system falls back gracefully if unavailable.
camera_1 = CameraManager(device_index=settings.CAMERA_1_DEVICE_INDEX)

# Backward-compatible alias — camera_0 is the "primary" camera.
# Existing code that imports `from camera_service.camera import camera`
# continues to work without any changes.
camera = camera_0
