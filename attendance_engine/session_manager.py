from uuid import UUID
from typing import Dict, Optional
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_factory
from models.attendance_session import AttendanceSession, SessionStatus
from models.attendance import Attendance, AttendanceStatus, AttendanceMethod
from models.student import Student
from backend.websocket.manager import manager

# Session modes
MODE_ATTENDANCE = "attendance"
MODE_HEADCOUNT = "headcount"


class SessionManager:
    """
    Manages active attendance sessions in memory for fast lookup
    by the Attendance Engine, and handles session lifecycle operations.

    Each active session stores:
        - course_id         : UUID of the course being attended
        - recognized_students: Set of student UUIDs already marked present this session
        - mode              : Current mode — "attendance" or "headcount"
        - latest_head_count : Most recent head count from Camera 1 (YOLOv8)
        - camera_1_available: Whether Camera 1 was successfully started
    """

    def __init__(self):
        # Maps session_id (str) -> dict of session state
        self.active_sessions: Dict[str, dict] = {}

    async def load_active_sessions(self):
        """Load any active sessions from DB on startup (ghost-session recovery)."""
        async with async_session_factory() as db:
            stmt = select(AttendanceSession).where(AttendanceSession.status == SessionStatus.ACTIVE)
            result = await db.execute(stmt)
            sessions = result.scalars().all()

            for session in sessions:
                self.active_sessions[str(session.id)] = {
                    "course_id": str(session.course_id),
                    "recognized_students": set(),
                    "mode": session.mode if hasattr(session, 'mode') else MODE_ATTENDANCE,
                    "latest_head_count": session.head_count,
                    "camera_1_available": False,  # Will be determined when engine starts
                }

                # Load already recognized students to prevent double-marking on recovery
                att_stmt = select(Attendance).where(
                    Attendance.session_id == session.id,
                    Attendance.status == AttendanceStatus.PRESENT
                )
                att_res = await db.execute(att_stmt)
                for record in att_res.scalars().all():
                    self.active_sessions[str(session.id)]["recognized_students"].add(str(record.student_id))

    def get_active_session(self) -> Optional[str]:
        """
        ClassOS assumes one classroom = one Pi = one active session at a time.
        Returns the ID of the current active session, or None.
        """
        if not self.active_sessions:
            return None
        return list(self.active_sessions.keys())[0]

    def get_mode(self, session_id: str) -> str:
        """Get the current mode for a session ('attendance' or 'headcount')."""
        if session_id not in self.active_sessions:
            return MODE_ATTENDANCE
        return self.active_sessions[session_id].get("mode", MODE_ATTENDANCE)

    def set_mode(self, session_id: str, mode: str):
        """Switch the session mode without losing any attendance data."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["mode"] = mode

    def set_camera_1_available(self, session_id: str, available: bool):
        """Record whether Camera 1 was successfully started."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["camera_1_available"] = available

    def is_camera_1_available(self, session_id: str) -> bool:
        """Check if Camera 1 is available for this session."""
        if session_id not in self.active_sessions:
            return False
        return self.active_sessions[session_id].get("camera_1_available", False)

    def get_head_count(self, session_id: str) -> int:
        """Get the latest head count from Camera 1."""
        if session_id not in self.active_sessions:
            return 0
        return self.active_sessions[session_id].get("latest_head_count", 0)

    def set_head_count(self, session_id: str, count: int):
        """Update the latest head count."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["latest_head_count"] = count

    def get_recognized_count(self, session_id: str) -> int:
        """Get the number of students recognized this session."""
        if session_id not in self.active_sessions:
            return 0
        return len(self.active_sessions[session_id].get("recognized_students", set()))

    def is_student_recognized(self, session_id: str, student_id: UUID) -> bool:
        """Check if student was already marked present this session."""
        if session_id not in self.active_sessions:
            return False
        return str(student_id) in self.active_sessions[session_id]["recognized_students"]

    def mark_student_recognized(self, session_id: str, student_id: UUID):
        """Update memory cache that student is recognized."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["recognized_students"].add(str(student_id))

    async def broadcast_event(self, session_id: str, event_type: str, payload: dict):
        """Send event to dashboard via WebSocket."""
        message = {
            "type": event_type,
            "data": payload
        }
        await manager.broadcast_to_session(session_id, message)


session_manager = SessionManager()
