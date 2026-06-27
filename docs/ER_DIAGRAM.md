# Database Entity-Relationship Diagram

This document outlines the relational database schema used by ClassOS, managed via PostgreSQL and SQLAlchemy.

## ER Diagram

```mermaid
erDiagram
    User {
        uuid id PK
        string email UK
        string password_hash
        enum role "ADMIN, TEACHER, STUDENT"
        timestamp created_at
        timestamp updated_at
    }

    Teacher {
        uuid id PK
        uuid user_id FK
        string first_name
        string last_name
        timestamp created_at
        timestamp updated_at
    }

    Student {
        uuid id PK
        uuid user_id FK
        string student_id UK
        string first_name
        string last_name
        string photo_path
        boolean face_registered
        boolean fingerprint_registered
        timestamp created_at
        timestamp updated_at
    }

    Course {
        uuid id PK
        uuid teacher_id FK
        string course_code UK
        string course_name
        string schedule
        timestamp created_at
        timestamp updated_at
    }

    Enrollment {
        uuid id PK
        uuid student_id FK
        uuid course_id FK
        timestamp created_at
        timestamp updated_at
    }

    AttendanceSession {
        uuid id PK
        uuid course_id FK
        uuid teacher_id FK
        enum status "ACTIVE, COMPLETED, CANCELLED"
        string mode "attendance, headcount"
        int head_count
        int recognized_count
        timestamp started_at
        timestamp ended_at
        timestamp created_at
        timestamp updated_at
    }

    Attendance {
        uuid id PK
        uuid session_id FK
        uuid student_id FK
        enum status "PRESENT, ABSENT, LATE, EXCUSED"
        enum method "FACE, FINGERPRINT, MANUAL"
        float confidence
        timestamp marked_at
        timestamp created_at
        timestamp updated_at
    }

    %% Relationships
    User ||--o| Teacher : "has profile"
    User ||--o| Student : "has profile"
    
    Teacher ||--o{ Course : "teaches"
    Teacher ||--o{ AttendanceSession : "manages"
    
    Course ||--o{ Enrollment : "has"
    Course ||--o{ AttendanceSession : "has sessions"
    
    Student ||--o{ Enrollment : "enrolled in"
    Student ||--o{ Attendance : "has attendance records"
    
    AttendanceSession ||--o{ Attendance : "contains"
```

## Description of Entities

1. **User**: The base authentication model. Every Teacher, Student, and Admin has a User account used for JWT login.
2. **Teacher**: Profile data for a teacher. Tied to a User account. Teachers manage Courses and Attendance Sessions.
3. **Student**: Profile data for a student. Tied to a User account. Contains boolean flags indicating if their facial embeddings or fingerprints have been successfully enrolled.
4. **Course**: Represents an academic class (e.g. `CS101`). 
5. **Enrollment**: A many-to-many join table mapping Students to Courses. Attendance sessions will only track students explicitly enrolled in the course.
6. **AttendanceSession**: A single real-world class meeting (e.g., today's lecture). 
   - `mode` — Current active mode: `"attendance"` (Camera 0 face recognition) or `"headcount"` (Camera 1 YOLOv8). Persisted so the engine can recover the correct mode after a restart or mode switch.
   - `head_count` — Latest head count from Camera 1 (YOLOv8), updated in real-time during head count mode.
   - `recognized_count` — Number of students auto-marked present (face or fingerprint). Updated each time a student is marked.
7. **Attendance (Record)**: A single student's attendance entry for a specific session. Tracks whether they were marked Present/Absent, and the exact method (Face vs Fingerprint) with the AI confidence score.

## Notes on Mode Field

The `mode` column on `AttendanceSession` stores the **last active** mode for the session. This allows the Attendance Engine to:
- Recover the correct camera assignment after a server restart
- Resume head count from where it left off
- Maintain consistent LCD display state

Modes:
| Value | Camera Used | AI Model | Purpose |
|-------|-------------|----------|---------|
| `"attendance"` | Camera 0 (CAM/DISP 0) | dlib face recognition | Mark students present via face/fingerprint |
| `"headcount"` | Camera 1 (CAM/DISP 1) | YOLOv8 Nano | Count total heads in classroom |
