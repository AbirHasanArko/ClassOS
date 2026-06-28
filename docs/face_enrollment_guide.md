# ClassOS — Face Enrollment & Camera Guide

This document covers:
1. [Student Face Registration](#1-student-face-registration)
2. [Gallery Upload (Phone / Desktop)](#2-gallery-upload-phone--desktop)
3. [Webcam Capture Across Device Types](#3-webcam-capture-across-device-types)
4. [USB Webcam Fallback for Attendance Cameras](#4-usb-webcam-fallback-for-attendance-cameras)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Student Face Registration

Students log in to their portal and navigate to **Face Registration**. There are two enrollment methods:

| Method | Best For | Notes |
|--------|----------|-------|
| **Upload Files** | Existing photos on phone/laptop gallery | Supports JPG, PNG, BMP, WebP |
| **Use Webcam** | Real-time capture | Works on phone, laptop, Pi browser |

**Recommended:** Upload **5–10 clear, front-facing photos** for best recognition accuracy. Avoid sunglasses or face coverings.

Each uploaded image is validated by the backend:
- Must contain **exactly one face**
- Generates a **128-dimensional dlib embedding** stored in the database
- The student is immediately marked as `face_registered = true` upon the first successful sample

---

## 2. Gallery Upload (Phone / Desktop)

### What Was Fixed (v2.1)

The most common cause of gallery upload failures was **EXIF orientation**. When a phone shoots in portrait mode, it stores the image sideways (landscape) and records the correct rotation in the EXIF metadata. The older code ignored this tag, so the AI received a sideways face and detected 0 faces → "failed to upload" error.

**v2.1 fix** (`ai_engine/embedding_generator.py`):
1. **EXIF auto-rotation** — The image is opened via Pillow and rotated/flipped according to its EXIF `Orientation` tag before being passed to the HOG face detector.
2. **Upsample retry** — If HOG finds 0 faces at the default scale (`upsample_num=1`), it retries at `upsample_num=2`, which catches faces that occupy a smaller portion of the frame (e.g., a wide-angle shot).
3. **RGB mode normalization** — Converts RGBA, palette, or grayscale images to RGB automatically.

### Pillow Compatibility

The EXIF fix relies on `Pillow`. The `Image.Transpose` enum (used for rotation) was introduced in **Pillow 9.1**. The code handles both old and new Pillow builds:

```python
try:
    _T = Image.Transpose      # Pillow 9.1+
    rotation_map = { 3: _T.ROTATE_180, 6: _T.ROTATE_270, 8: _T.ROTATE_90 }
except AttributeError:
    rotation_map = { 3: 3, 6: 4, 8: 5 }  # Pillow <9.1 integer constants
```

`requirements.txt` now pins `Pillow>=9.1.0` explicitly.

### Supported EXIF Orientation Values

| EXIF Value | Meaning | Applied Transform |
|-----------|---------|-------------------|
| 1 | Normal (upright) | None |
| 3 | Rotated 180° | `ROTATE_180` |
| 6 | Rotated 90° CW | `ROTATE_270` |
| 8 | Rotated 90° CCW | `ROTATE_90` |
| 2 | Mirrored horizontal | `FLIP_LEFT_RIGHT` |
| 4 | Mirrored vertical | `FLIP_TOP_BOTTOM` |

---

## 3. Webcam Capture Across Device Types

### The Problem

The original webcam code used `getUserMedia({ video: { facingMode: 'user' } })`. This works on phones and laptops but **fails silently on Raspberry Pi**, because the CSI Camera Module does not advertise a `facingMode` in Chromium's device enumeration — it has no concept of "front" or "rear". The browser would either:
- Fail with `OverconstrainedError` (no matching device)
- Return an empty stream

### The Fix (v2.1)

**`frontend/src/components/ui/WebcamCapture.jsx`** now uses a two-step strategy:

```
Step 1: Try facingMode: 'user'
        → Works on mobile (selects front/selfie camera) ✅
        → Works on laptop (selects built-in webcam) ✅
        → Fails on Pi → OverconstrainedError

Step 2: On OverconstrainedError, retry without facingMode constraint
        → Pi browser picks the first available device = /dev/video0 = Camera 0 ✅
```

### Device Behavior Summary

| Device | facingMode: 'user' result | Final camera used |
|--------|--------------------------|-------------------|
| iPhone / Android | ✅ Selects front/selfie camera | Front camera |
| Laptop | ✅ Selects built-in webcam | Built-in webcam |
| Raspberry Pi (Chromium) | ❌ `OverconstrainedError` → retries | `/dev/video0` (Camera 0) |
| Desktop with external webcam | ✅ Selects default webcam | Default webcam |

> **Note:** The Retry button in the UI (`startStream()`) also uses this same two-step logic.

---

## 4. USB Webcam Fallback for Attendance Cameras

### Overview

In previous versions, if Camera 0 (`/dev/video0`) or Camera 1 (`/dev/video2`) failed to open, the system would throw a `RuntimeError` and crash the backend startup.

**v2.1** introduces a **probe-and-fallback** mechanism in `camera_service/camera.py`. When a preferred camera device cannot be opened, the system automatically tries a configurable list of fallback device indices and uses the first one that opens.

### How It Works

`CameraManager` now accepts a `fallback_indices` list. At startup, it probes devices in this order:

```
preferred_index → fallback[0] → fallback[1] → ... → RuntimeError (if none open)
```

Example startup log when CSI camera is missing but USB webcam is on `/dev/video1`:
```
Trying camera device index 0...
⚠️  Preferred camera /dev/video0 unavailable. Fell back to /dev/video1 (USB webcam).
```

### Configuration

Set `CAMERA_USB_FALLBACK_INDICES` in your `.env` file:

```bash
# Single USB webcam on /dev/video1
CAMERA_USB_FALLBACK_INDICES=1

# Try /dev/video1, then /dev/video3, then /dev/video4
CAMERA_USB_FALLBACK_INDICES=1,3,4
```

**Default:** `1,3,4` (probes the three most common USB webcam indices after the two CSI cameras).

### Docker Device Mapping

When using a USB webcam, add its device node to `docker-compose.yml`:

```yaml
backend:
  devices:
    - /dev/video0:/dev/video0       # Camera 0 preferred (CSI)
    - /dev/video1:/dev/video1       # USB webcam fallback
    - /dev/video2:/dev/video2       # Camera 1 preferred (CSI)
    - /dev/ttyS0:/dev/ttyS0
    - /dev/i2c-1:/dev/i2c-1
  privileged: true
```

### Camera Mutual Exclusivity

Camera 0 and Camera 1 are **never running at the same time**:
- **Attendance mode**: Camera 0 runs, Camera 1 is stopped
- **Head Count mode**: Camera 1 runs, Camera 0 is stopped

This means even if both cameras fall back to the **same USB webcam**, there is no device conflict — the previous camera is always fully stopped and released before the next one starts.

### Verify Which Camera Is Active

Check the backend logs:
```bash
docker compose logs backend | grep "Camera opened\|Fell back"
```

Expected output:
```
✅ Camera opened on preferred device /dev/video0
⚠️  Preferred camera /dev/video2 unavailable. Fell back to /dev/video1 (USB webcam).
```

---

## 5. Troubleshooting

### Gallery Upload: "failed to upload face images"

| Cause | Solution |
|-------|---------|
| Photo taken in portrait mode (EXIF) | Fixed automatically in v2.1 — ensure you are running the latest build |
| Multiple faces in the image | Use a photo with only your face, no other people in the background |
| Image file is corrupt | Try a different image |
| Image format not supported | Use JPG, PNG, BMP, or WebP |

The error message now shows the **actual per-file reason** from the server (e.g., "could not extract a face"), not just the generic fallback message.

### Webcam: "No camera device found"

- Ensure you are on HTTPS (or `localhost`) — browsers block `getUserMedia` on plain HTTP
- On iPhone: you must install and trust the self-signed certificate — see [camera_permissions_guide.md](camera_permissions_guide.md)
- On Raspberry Pi Chromium: Camera 0 must be detected. Run `ls /dev/video*` to confirm

### Attendance Camera Doesn't Start

1. Check backend logs: `docker compose logs backend | grep "Trying camera\|Fell back\|unavailable"`
2. Verify the device is accessible: `ls -la /dev/video*`
3. Ensure the device is mapped in `docker-compose.yml` under `devices:`
4. Check `CAMERA_USB_FALLBACK_INDICES` in `.env` includes the correct index
