import cv2
import threading
import time
import numpy as np
from typing import Optional

from backend.config import settings

class CameraManager:
    def __init__(self):
        self.width, self.height = settings.camera_resolution
        self.fps = settings.CAMERA_FPS
        self.mock_mode = settings.CAMERA_MOCK_MODE
        
        self.cap = None
        self.picam2 = None
        
        # Buffer for the latest frame
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        
        self._running = False
        self._thread = None
        
        # Try to import picamera2 if not in mock mode
        if not self.mock_mode:
            try:
                from picamera2 import Picamera2
                self.picam2 = Picamera2()
            except ImportError:
                print("Warning: picamera2 not found. Falling back to OpenCV mock mode.")
                self.mock_mode = True

    def start(self):
        """Start the camera and the background frame-grabbing thread."""
        if self._running:
            return
            
        print("Starting camera service...")
        if self.mock_mode:
            # Open default webcam via OpenCV
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            if not self.cap.isOpened():
                raise RuntimeError("Could not open mock webcam.")
        else:
            # Initialize Pi Camera 3
            config = self.picam2.create_video_configuration(
                main={"size": (self.width, self.height), "format": "BGR888"},
                align_to_16=False
            )
            self.picam2.configure(config)
            self.picam2.start()

        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self):
        """Daemon thread loop that constantly updates the latest frame buffer."""
        while self._running:
            if self.mock_mode:
                ret, frame = self.cap.read()
                if ret:
                    with self._lock:
                        self._latest_frame = frame
            else:
                # Capture directly into numpy array
                frame = self.picam2.capture_array()
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
        """Stop the camera and cleanup resources."""
        if not self._running:
            return
            
        print("Stopping camera service...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            
        if self.mock_mode and self.cap:
            self.cap.release()
        elif not self.mock_mode and self.picam2:
            self.picam2.stop()

# Singleton instance
camera = CameraManager()
