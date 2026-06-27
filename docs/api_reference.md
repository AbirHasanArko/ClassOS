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

## Users

### `GET /users/` 🔒 (Admin)
List all system users (Teachers and Admins).

### `POST /users/` 🔒 (Admin)
Create a new user.

### `PUT /users/{user_id}` 🔒 (Admin)
Update user details or password.

### `DELETE /users/{user_id}` 🔒 (Admin)
Delete a user.

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

### `PUT /students/{student_id}` 🔒 (Admin/Teacher)
Update a student's profile information.

### `DELETE /students/{student_id}` 🔒 (Admin/Teacher)
Delete a student and all their associated data, enrollments, and biometrics.

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

### `POST /students/{student_id}/face` 🔒 (Admin/Teacher/Student)
Upload one or more face images to register a student's face.

Each image must contain exactly one clearly visible face. The system generates a 128D embedding from each and stores it for live recognition. Up to 20 samples per student.

**Request:** `multipart/form-data` with `files` field (one or more image files: jpg, png, bmp, webp).

> 💡 **Camera Sources**: Any browser-accessible camera works for enrollment — laptop webcam, USB webcam attached to a teacher's device, or a phone camera via the mobile browser. Camera 0 on the Pi is used for live attendance scanning, NOT for enrollment.

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
Delete all face embeddings and images for a student, resetting their face registration.

**Response (200):**
```json
{
  "message": "Deleted 5 face sample(s) for John Doe. Face registration has been reset.",
  "deleted_count": 5
}
```

---

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

### `PUT /courses/{course_id}` 🔒 (Admin/Teacher)
Update course details.

### `DELETE /courses/{course_id}` 🔒 (Admin/Teacher)
Delete a course. Cascades and removes all attendance sessions and enrollments associated with it.

### `POST /courses/{course_id}/enroll` 🔒 (Admin/Teacher)
Enroll students in a course.

**Request:**
```json
{
  "student_ids": ["uuid1", "uuid2"]
}
```

### `POST /students/me/courses/{course_id}/enroll` 🔒 (Student)
Self-enroll into a course.

### `DELETE /students/me/courses/{course_id}/enroll` 🔒 (Student)
Self-unenroll from a course.

---

## Attendance

### `POST /attendance/sessions` 🔒 (Admin/Teacher)
Start a new attendance session.

**Request:**
```json
{
  "course_id": "uuid",
  "mode": "attendance"
}
```

**Mode options:**
- `"attendance"` (default) — Take Attendance mode (Camera 0, face recognition)
- `"headcount"` — Verify Head Count mode (Camera 1, YOLOv8)

**Response (201):** `SessionOut` with `mode`, `head_count`, `recognized_count` fields.

### `POST /attendance/sessions/{session_id}/end` 🔒 (Admin/Teacher)
End an active session. Stops cameras and AI pipeline.

### `POST /attendance/sessions/{session_id}/mode` 🔒 (Admin/Teacher)
Switch the active mode for a running session without losing any attendance data.

**Request:**
```json
{
  "mode": "headcount"
}
```

**Response (200):**
```json
{
  "session_id": "uuid",
  "mode": "headcount",
  "present_count": 15,
  "head_count": 17,
  "camera_1_available": true
}
```

> 💡 **Mode Switching**: All `recognized_students` data is preserved when switching modes. The engine automatically starts/stops the appropriate camera.

### `POST /attendance/sessions/{session_id}/attendance` 🔒 (Admin/Teacher)
Manually mark attendance for a student.

**Request:**
```json
{
  "student_id": "uuid",
  "status": "present"
}
```

### `GET /attendance/sessions/{session_id}/roster` 🔒 (Admin/Teacher)
Get the full attendance roster for a session.

**Response:** List of `AttendanceRosterItemOut` with student names, status, method, confidence, and marked_at.

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

> 💡 **Direct Scan**: This endpoint can be called at any time during a Take Attendance session — not just when a low-confidence face is detected. Students with no face detection (e.g., hijab, mask) can use this directly.

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

Connect to receive real-time attendance events for a session.

**Event Types:**

| Type | Data | Description |
|------|------|-------------|
| `attendance_marked` | `{student_id, student_name, method, confidence}` | Student marked present (includes full name) |
| `fingerprint_required` | `{student_id, confidence, message}` | Low confidence (30–69%) — needs fingerprint |
| `unknown_face` | `{confidence}` | Unrecognized face detected (<30%) |
| `head_count_update` | `{head_count, present_count, is_match}` | Head count result from Camera 1 |
| `mode_switched` | `{mode, present_count, head_count}` | Session mode changed |
| `camera_1_unavailable` | `{message}` | Camera 1 failed to start |
| `lcd_update` | `{line1, line2, line3, line4}` | LCD content mirror (20 chars per line) |

> 💡 **LCD Mirror**: The `lcd_update` event allows the dashboard to replicate exactly what the physical LCD displays in real-time.

---

## Video Streams

### `GET /stream/live`
**Camera 0** MJPEG stream — face recognition feed.
Returns `multipart/x-mixed-replace` continuous stream.
Used during **Take Attendance** mode.

Use in HTML: `<img src="/api/stream/live" />`

### `GET /stream/headcount`
**Camera 1** MJPEG stream — head counting feed.
Returns `multipart/x-mixed-replace` continuous stream.
Used during **Verify Head Count** mode.
If Camera 1 is unavailable, the stream will be empty.

Use in HTML: `<img src="/api/stream/headcount" />`

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
