"""
ClassOS — Camera Hardware Test Script
Run with: python -m scripts.test_camera
"""

import time
import sys


def test_camera():
    print("=" * 50)
    print("  ClassOS — Camera Test")
    print("=" * 50)

    # 1. Import test
    print("\n[1/4] Importing camera service...")
    try:
        from camera_service.camera import camera
        print("  ✅ Import successful")
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        sys.exit(1)

    # 2. Start camera
    print(f"\n[2/4] Starting camera (device index {camera.device_index})...")
    try:
        camera.start()
        print("  ✅ Camera started")
    except RuntimeError as e:
        print(f"  ❌ Camera start failed: {e}")
        print("  Hint: Check that the USB webcam is connected and /dev/video0 exists.")
        sys.exit(1)

    # 3. Capture a frame
    print("\n[3/4] Capturing test frame (waiting 2 seconds for warm-up)...")
    time.sleep(2)
    frame = camera.get_latest_frame()

    if frame is not None:
        h, w, c = frame.shape
        print(f"  ✅ Frame captured: {w}x{h}, {c} channels")
    else:
        print("  ❌ No frame captured — camera may not be functioning")
        camera.stop()
        sys.exit(1)

    # 4. Test face detection (optional, may fail if no face is visible)
    print("\n[4/4] Testing face detection on captured frame...")
    try:
        from ai_engine.face_detector import detector
        faces = detector.detect_faces(frame)
        print(f"  ✅ Detected {len(faces)} face(s) in frame")
    except Exception as e:
        print(f"  ⚠️  Face detection skipped: {e}")

    # Cleanup
    camera.stop()

    print("\n" + "=" * 50)
    print("  Camera test PASSED ✅")
    print("=" * 50)


if __name__ == "__main__":
    test_camera()
