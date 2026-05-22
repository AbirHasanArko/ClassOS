import asyncio
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_factory
from models.attendance import Attendance, AttendanceStatus, AttendanceMethod
from models.attendance_session import AttendanceSession
from attendance_engine.session_manager import session_manager
from ai_engine.pipeline import pipeline
from ai_engine.config import ai_config
from camera_service.camera import camera

class AttendanceEngine:
    """
    The main orchestrator. Links the AI pipeline outputs to the database
    and WebSocket manager based on the active session.
    """
    def __init__(self):
        self.is_running = False
        
    async def start(self):
        """Start the engine loop."""
        if self.is_running:
            return
            
        print("Starting Attendance Engine...")
        await session_manager.load_active_sessions()
        await pipeline.initialize()
        
        self.is_running = True
        
        # Start the background task that consumes AI results
        # In a real async architecture, pipeline.process_frame would be called
        # by a dedicated consumer thread. Since pipeline is synchronous, we use a bridge.
        asyncio.create_task(self._engine_loop())

    async def _engine_loop(self):
        """Background loop that processes frames if a session is active."""
        camera.start()
        
        while self.is_running:
            session_id = session_manager.get_active_session()
            
            if session_id:
                frame = camera.get_latest_frame()
                if frame is not None:
                    # process_frame is currently synchronous and blocks this loop briefly.
                    # We pass a callback wrapper to handle the results asynchronously.
                    def sync_callback(result):
                        # Schedule the async handler safely
                        asyncio.create_task(self._handle_ai_result(session_id, result))
                        
                    pipeline.is_running = True
                    pipeline.process_frame(frame, sync_callback)
                else:
                    await asyncio.sleep(0.1)
            else:
                # No active session, idle
                pipeline.is_running = False
                await asyncio.sleep(1.0)

    async def _handle_ai_result(self, session_id: str, result: dict):
        """Process output from the AI Pipeline."""
        
        if result["type"] == "recognition":
            student_id_str = str(result["student_id"])
            confidence = result["confidence"]
            
            # If already recognized this session, ignore to save DB writes
            if session_manager.is_student_recognized(session_id, result["student_id"]):
                return
                
            if confidence >= ai_config.FACE_CONFIDENCE_AUTO:
                # 1. High confidence -> Auto mark present
                await self._mark_attendance(
                    session_id=session_id,
                    student_id=result["student_id"],
                    method=AttendanceMethod.FACE,
                    confidence=confidence
                )
                
            elif confidence >= ai_config.FACE_CONFIDENCE_FINGERPRINT:
                # 2. Medium confidence -> Trigger fingerprint flow
                # We broadcast this so the dashboard shows a prompt
                await session_manager.broadcast_event(session_id, "fingerprint_required", {
                    "student_id": student_id_str,
                    "confidence": confidence,
                    "message": "Low confidence face detected. Please use fingerprint sensor."
                })
                
            else:
                # 3. Low confidence -> Unknown
                await session_manager.broadcast_event(session_id, "unknown_face", {
                    "confidence": confidence
                })
                
        elif result["type"] == "head_count":
            # Check for mismatch
            count = result["count"]
            recognized = result["recognized_count"]
            
            if count > recognized:
                await session_manager.broadcast_event(session_id, "head_count_mismatch", {
                    "head_count": count,
                    "recognized_count": recognized,
                    "warning": "More people detected than recognized faces."
                })

    async def _mark_attendance(self, session_id: str, student_id: UUID, method: AttendanceMethod, confidence: float):
        """Write attendance to DB and notify dashboard."""
        
        async with async_session_factory() as db:
            # Update record
            stmt = select(Attendance).where(
                Attendance.session_id == UUID(session_id),
                Attendance.student_id == student_id
            )
            res = await db.execute(stmt)
            record = res.scalar_one_or_none()
            
            if record and record.status != AttendanceStatus.PRESENT:
                record.status = AttendanceStatus.PRESENT
                record.method = method
                record.confidence = confidence
                record.marked_at = datetime.now(timezone.utc)
                
                # Update session recognized count
                sess_stmt = select(AttendanceSession).where(AttendanceSession.id == UUID(session_id))
                sess_res = await db.execute(sess_stmt)
                session = sess_res.scalar_one()
                session.recognized_count += 1
                
                await db.commit()
                
                # Update memory cache
                session_manager.mark_student_recognized(session_id, student_id)
                
                # Broadcast success to dashboard
                await session_manager.broadcast_event(session_id, "attendance_marked", {
                    "student_id": str(student_id),
                    "method": method.value,
                    "confidence": confidence
                })

engine = AttendanceEngine()
