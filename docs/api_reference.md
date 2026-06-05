# ClassOS — API Reference

## Base URL

```
http://localhost:8000/api
```

In production (via Nginx): `http://<pi-ip>/api`

---

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### `POST /auth/login`
Authenticate and receive JWT tokens.

**Request:**
```json
{
  "email": "admin@classos.local",
  "password": "changeme123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@classos.local",
    "role": "admin",
    "name": "System Administrator"
  }
}
```

### `POST /auth/refresh`
Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

### `POST /auth/logout` 🔒
Invalidate session (client discards token).

---

## Students

### `GET /students/` 🔒
List students with optional search and pagination.

**Query Params:** `skip`, `limit`, `search`

### `POST /students/` 🔒 (Admin/Teacher)
Create a new student.

**Request:**
```json
{
  "student_id": "2024-CS-001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@university.edu"
}
```

### `GET /students/{student_id}` 🔒
Get student details by UUID.

---

## Face Registration

### `GET /students/{student_id}/face` 🔒
Get face registration status and sample count for a student.

**Response (200):**
```json
{
  "student_id": "uuid",
  "face_registered": true,
  "total_samples": 5,
  "max_samples": 20,
  "samples": [
    { "id": "uuid", "student_id": "uuid", "image_path": "data/faces/...", "sample_number": 1 }
  ]
}
```

### `POST /students/{student_id}/face` 🔒 (Admin/Teacher)
Upload one or more face images to register a student's face.

Each image must contain exactly one clearly visible face. The system generates a 128D embedding from each and stores it for live recognition. Up to 20 samples per student.

**Request:** `multipart/form-data` with `files` field (one or more image files: jpg, png, bmp, webp).

**Response (201):**
```json
{
  "message": "Added 3 face sample(s) for John Doe.",
  "samples_added": 3,
  "total_samples": 3,
  "face_registered": true
}
```

### `DELETE /students/{student_id}/face` 🔒 (Admin/Teacher)
Delete all face embeddings and images for a student, resetting their face registration. Use when a student's appearance has changed significantly.

**Response (200):**
```json
{
  "message": "Deleted 5 face sample(s) for John Doe. Face registration has been reset.",
  "deleted_count": 5
}
```

## Courses

### `GET /courses/` 🔒
List courses.

### `POST /courses/` 🔒 (Admin/Teacher)
Create a course.

**Request:**
```json
{
  "course_code": "CS101",
  "course_name": "Intro to CS",
  "schedule": "Mon/Wed 10:00-11:30"
}
```

### `POST /courses/{course_id}/enroll` 🔒 (Admin/Teacher)
Enroll students in a course.

**Request:**
```json
{
  "student_ids": ["uuid1", "uuid2"]
}
```

---

## Attendance

### `POST /attendance/sessions` 🔒 (Admin/Teacher)
Start a new attendance session.

**Request:**
```json
{
  "course_id": "uuid"
}
```

### `POST /attendance/sessions/{session_id}/end` 🔒 (Admin/Teacher)
End an active session.

### `POST /attendance/sessions/{session_id}/attendance` 🔒 (Admin/Teacher)
Manually mark attendance.

**Request:**
```json
{
  "student_id": "uuid",
  "status": "present"
}
```

---

## Fingerprint

### `GET /fingerprint/status`
Check sensor connectivity.

### `POST /fingerprint/enroll` 🔒 (Admin/Teacher)
Enroll a student's fingerprint.

**Request:**
```json
{
  "student_id": "uuid"
}
```

### `POST /fingerprint/verify`
Scan and verify a fingerprint. Returns matched student.

---

## Analytics

### `GET /analytics/dashboard/stats` 🔒 (Admin/Teacher)
Get attendance statistics.

---

## System

### `GET /system/status`
System resource usage (CPU, memory, disk).

### `GET /health`
Health check endpoint.

---

## WebSocket

### `WS /ws/attendance/{session_id}?token=<jwt>`

Connect to receive real-time attendance events.

**Event Types:**

| Type | Data | Description |
|------|------|-------------|
| `attendance_marked` | `{student_id, method, confidence}` | Student marked present |
| `fingerprint_required` | `{student_id, confidence, message}` | Low confidence — needs fingerprint |
| `unknown_face` | `{confidence}` | Unrecognized face detected |
| `head_count_mismatch` | `{head_count, recognized_count, warning}` | More people than recognized |

---

## Video Stream

### `GET /stream/live`
MJPEG video stream endpoint. Returns `multipart/x-mixed-replace` continuous stream.

Use in HTML: `<img src="/api/stream/live" />`

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Unauthorized / invalid token |
| 403 | Forbidden / insufficient role |
| 404 | Resource not found |
| 500 | Internal server error |

---

🔒 = Requires authentication
