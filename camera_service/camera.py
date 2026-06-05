import cv2
import threading
import time
import numpy as np
from typing import Optional

from backend.config import settings


class CameraManager:
    """Manages a USB webcam via OpenCV's VideoCapture.

    Runs a background thread that continuously grabs frames into a buffer.
    Consumers call ``get_latest_frame()`` to read the most recent capture.
    """

    def __init__(self):
        self.width, self.height = settings.camera_resolution
        self.fps = settings.CAMERA_FPS
        self.device_index = settings.CAMERA_DEVICE_INDEX

        self.cap: Optional[cv2.VideoCapture] = None

        # Buffer for the latest frame
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()

        self._running = False
        self._thread = None

    def start(self):
        """Start the USB webcam and the background frame-grabbing thread."""
        if self._running:
            return

        print(f"Starting camera service (device index {self.device_index})...")
        self.cap = cv2.VideoCapture(self.device_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open USB webcam at device index {self.device_index}. "
                "Check that the camera is connected and not in use by another process."
            )

        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

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

        print("Stopping camera service...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()
            self.cap = None


# Singleton instance
camera = CameraManager()
