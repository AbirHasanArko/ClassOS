# ClassOS — Testing Guide

## Overview

ClassOS testing is organized into three layers:

1. **Unit tests** — Individual module logic
2. **Integration tests** — API endpoints with database
3. **Hardware tests** — Camera and fingerprint sensor on Pi 5

---

## 1. Unit Tests

### Running Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest backend/tests/ -v

# Run specific module
python -m pytest backend/tests/test_auth.py -v

# With coverage
python -m pytest backend/tests/ --cov=backend --cov-report=html
```

### What to Test

| Module | Tests |
|--------|-------|
| `backend/auth/password.py` | Hash/verify password, bcrypt rounds |
| `backend/auth/jwt_handler.py` | Token creation, verification, expiry |
| `ai_engine/face_recognizer.py` | Confidence calculation, embedding matching |
| `ai_engine/head_counter.py` | Model loading, person detection |
| `attendance_engine/session_manager.py` | Session lifecycle, duplicate prevention |

---

## 2. Integration Tests

Integration tests require a running PostgreSQL instance.

### Setup Test Database

```bash
# Start only the database via Docker
docker compose up -d db

# Set test database URL
export DATABASE_URL="postgresql+asyncpg://classos:classos_secret@localhost:5432/classos_db"
```

### Run Integration Tests

```bash
python -m pytest backend/tests/integration/ -v
```

### Key Integration Test Scenarios

1. **Auth Flow**:
   - Login with valid credentials → receive tokens
   - Login with invalid credentials → 401
   - Access protected endpoint with valid token → 200
   - Access protected endpoint without token → 401
   - Refresh expired access token → new tokens

2. **Student CRUD**:
   - Create student → verify in DB
   - List students with pagination
   - Search students by name/ID
   - Create duplicate student ID → 400

3. **Attendance Session**:
   - Start session → verify active in DB
   - Start duplicate session for same course → 400
   - End session → verify completed status
   - Mark attendance manually

---

## 3. Hardware Tests (Raspberry Pi 5)

### Camera Test

```bash
# Quick test
python3 -c "
from camera_service.camera import camera
camera.start()
import time
time.sleep(2)
frame = camera.get_latest_frame()
print('Frame shape:', frame.shape if frame is not None else 'None')
camera.stop()
print('Camera test passed!')
"
```

### Fingerprint Sensor Test

```bash
# Connection test
python3 -c "
from fingerprint_service.sensor import fp_sensor
status = fp_sensor.get_status()
print('Sensor connected:', status)
print('Mock mode:', fp_sensor.mock_mode)
"
```

### Full Pipeline Test

```bash
# Test face detection on a sample image
python3 -c "
import cv2
from ai_engine.face_detector import detector

# Use a sample image
img = cv2.imread('test_image.jpg')
if img is not None:
    faces = detector.detect_faces(img)
    print(f'Detected {len(faces)} faces')
else:
    print('No test image found')
"
```

---

## 4. Frontend Tests

### Build Verification

```bash
cd frontend
npm run build
# Should complete without errors
```

### Manual UI Testing Checklist

- [ ] Login page renders correctly
- [ ] Login with valid credentials redirects to dashboard
- [ ] Login with invalid credentials shows error
- [ ] Sidebar navigation works for all pages
- [ ] Dark/light theme toggle works
- [ ] Student list loads and displays data
- [ ] Add student modal creates student
- [ ] Course list loads
- [ ] Add course modal creates course
- [ ] Attendance page shows course selector
- [ ] Start session activates camera feed
- [ ] WebSocket connection established (green indicator)
- [ ] Attendance log updates in real-time
- [ ] End session stops camera feed
- [ ] Analytics charts render
- [ ] Settings page shows profile and theme toggle

---

## 5. End-to-End Test

Full workflow test (requires Pi 5 with hardware):

1. Login as admin → Create a teacher account
2. Login as teacher → Create a course
3. Register a student → Capture 20 face samples → Enroll fingerprint
4. Enroll student in course
5. Start attendance session
6. Stand in front of camera → Verify face recognition
7. Cover face → Verify fingerprint prompt appears
8. Use fingerprint sensor → Verify attendance marked
9. End session → Verify attendance records in DB
10. Check analytics page → Verify charts updated
