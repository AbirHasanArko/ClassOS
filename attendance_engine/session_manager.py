from uuid import UUID
from typing import Dict, Optional
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_factory
from models.attendance_session import AttendanceSession, SessionStatus
from models.attendance import Attendance, AttendanceStatus, AttendanceMethod
from backend.websocket.manager import manager

class SessionManager:
    """
    Manages active attendance sessions in memory for fast lookup
    by the Attendance Engine, and handles session lifecycle operations.
    """
    def __init__(self):
        # Maps session_id (str) -> dict of session state
        self.active_sessions: Dict[str, dict] = {}
        
    async def load_active_sessions(self):
        """Load any active sessions from DB on startup (recovery)."""
        async with async_session_factory() as db:
            stmt = select(AttendanceSession).where(AttendanceSession.status == SessionStatus.ACTIVE)
            result = await db.execute(stmt)
            sessions = result.scalars().all()
            
            for session in sessions:
                self.active_sessions[str(session.id)] = {
                    "course_id": str(session.course_id),
                    "recognized_students": set() # To prevent duplicate DB writes
                }
                
                # Load already recognized students
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

    def is_student_recognized(self, session_id: str, student_id: UUID) -> bool:
        """Check if student was already marked present this session to avoid spamming DB."""
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
