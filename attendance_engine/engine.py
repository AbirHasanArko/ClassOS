import asyncio
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import async_session_factory
from models.attendance import Attendance, AttendanceStatus, AttendanceMethod
from models.attendance_session import AttendanceSession
from models.student import Student
from attendance_engine.session_manager import session_manager, MODE_ATTENDANCE, MODE_HEADCOUNT
from ai_engine.pipeline import face_pipeline, head_count_pipeline
from ai_engine.config import ai_config
import logging
import sys
from camera_service.camera import camera_0, camera_1

logger = logging.getLogger("classos.engine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)




class AttendanceEngine:
    """
    The main orchestrator. Links the AI pipeline outputs to the database
    and WebSocket manager based on the active session and its current mode.

    Dual-camera support:
        - Take Attendance mode (mode="attendance"):
            Camera 0 → FaceRecognitionPipeline → mark students present
            Fingerprint scanner always available as direct fallback
        - Verify Head Count mode (mode="headcount"):
            Camera 1 → HeadCountPipeline → compare head count vs recognized count

    Mode switches are handled transparently — the engine detects the current
    mode each iteration, starts/stops the appropriate camera, and preserves
    all session data (recognized_students, etc.) across mode changes.

    LCD integration:
        The engine imports lcd_display lazily to avoid crashing on non-Pi hardware.
        All LCD calls are wrapped in try/except so hardware failures are non-fatal.
    """

    def __init__(self):
        self.is_running = False
        self._lcd = None  # Lazy-loaded

    @property
    def lcd(self):
        """Lazy-load the LCD display service (graceful if hardware unavailable)."""
        if self._lcd is None:
            try:
                from lcd_service.display import lcd_display
                self._lcd = lcd_display
            except Exception as e:
                logger.error(f"Failed to load LCD service: {e}")
                self._lcd = None
        return self._lcd

    async def start(self):
        """Start the engine loop."""
        if self.is_running:
            return

        logger.info("Starting Attendance Engine...")
        await session_manager.load_active_sessions()

        # Initialize AI models
        await face_pipeline.initialize()
        head_count_pipeline.initialize()

        self.is_running = True
        if self.lcd: self.lcd.show_idle()

        # Start the background task that consumes AI results
        asyncio.create_task(self._engine_loop())

        # Show idle screen on LCD
        self._lcd_show_idle()

    async def _engine_loop(self):
        """
        Background loop that processes frames if a session is active.

        Each iteration:
        1. Checks if there is an active session
        2. Reads the current mode (attendance vs headcount)
        3. Manages the correct camera (start/stop as needed)
        4. Runs the correct AI pipeline
        5. The pipeline callback schedules async result handling on the event loop
        """
        current_mode = None  # Tracks mode to detect switches and manage cameras

        while self.is_running:
            session_id = session_manager.get_active_session()

            if session_id:
                mode = session_manager.get_mode(session_id)

                # ── Handle mode switches ──────────────────────────────────────
                if mode != current_mode:
                    await self._handle_mode_switch(session_id, old_mode=current_mode, new_mode=mode)
                    current_mode = mode

                # ── Run the pipeline for the current mode ─────────────────────
                if mode == MODE_ATTENDANCE:
                    await self._run_attendance_step(session_id)
                elif mode == MODE_HEADCOUNT:
                    await self._run_headcount_step(session_id)

            else:
                # No active session — release all cameras and show idle on LCD
                if camera_0._running:
                    camera_0.stop()
                if camera_1._running:
                    camera_1.stop()
                face_pipeline.is_running = False
                head_count_pipeline.is_running = False
                current_mode = None
                self._lcd_show_idle()
                await asyncio.sleep(1.0)

    async def _handle_mode_switch(self, session_id: str, old_mode: str, new_mode: str):
        """
        Handle camera and pipeline state transitions when mode changes.
        Attendance data (recognized_students) is preserved across switches.
        """
        print(f"Session {session_id[:8]}: mode switch {old_mode} → {new_mode}")

        if new_mode == MODE_ATTENDANCE:
            # Stop Camera 1 / head count pipeline
            if camera_1._running:
                camera_1.stop()
            head_count_pipeline.is_running = False

            # Start Camera 0 / face recognition pipeline
            if not camera_0._running:
                camera_0.start_if_available()
            face_pipeline.is_running = True

        elif new_mode == MODE_HEADCOUNT:
            # Stop Camera 0 / face recognition pipeline
            if camera_0._running:
                camera_0.stop()
            face_pipeline.is_running = False

            # Start Camera 1 / head count pipeline
            cam1_ok = camera_1.start_if_available()
            session_manager.set_camera_1_available(session_id, cam1_ok)
            head_count_pipeline.is_running = cam1_ok

            if not cam1_ok:
                # Camera 1 unavailable — notify the dashboard
                await session_manager.broadcast_event(session_id, "camera_1_unavailable", {
                    "message": "Camera 1 (head count camera) is not available on this device."
                })

        # Broadcast mode switch event to dashboard
        recognized_count = session_manager.get_recognized_count(session_id)
        head_count = session_manager.get_head_count(session_id)
        await session_manager.broadcast_event(session_id, "mode_switched", {
            "mode": new_mode,
            "present_count": recognized_count,
            "head_count": head_count,
        })

        # Update LCD
        if new_mode == MODE_HEADCOUNT:
            self._lcd_show_headcount(recognized_count, head_count)

    async def _run_attendance_step(self, session_id: str):
        """Process one frame from Camera 0 through the face recognition pipeline."""
        if not camera_0._running:
            camera_0.start_if_available()

        frame = camera_0.get_latest_frame()
        if frame is not None:
            loop = asyncio.get_running_loop()

            def sync_callback(result):
                asyncio.run_coroutine_threadsafe(
                    self._handle_ai_result(session_id, result),
                    loop
                )

            face_pipeline.is_running = True
            try:
                await asyncio.to_thread(face_pipeline.process_frame, frame, sync_callback)
            except Exception as e:
                print(f"Error in face_pipeline.process_frame: {e}")
        else:
            await asyncio.sleep(0.1)

    async def _run_headcount_step(self, session_id: str):
        """Process one frame from Camera 1 through the head count pipeline."""
        cam1_available = session_manager.is_camera_1_available(session_id)
        
        frame = None
        if cam1_available:
            if not camera_1._running:
                cam1_ok = camera_1.start_if_available()
                if not cam1_ok:
                    session_manager.set_camera_1_unavailable(session_id)
                    await session_manager.broadcast_event(session_id, "camera_1_unavailable", {})
                    cam1_available = False
            
            if cam1_available:
                frame = camera_1.get_latest_frame()

        # Fallback to Camera 0 (primary) if Camera 1 is missing or failed
        if not cam1_available:
            if not camera_0._running:
                camera_0.start_if_available()
            frame = camera_0.get_latest_frame()

        if frame is not None:
            loop = asyncio.get_running_loop()

            def sync_callback(result):
                asyncio.run_coroutine_threadsafe(
                    self._handle_ai_result(session_id, result),
                    loop
                )

            head_count_pipeline.is_running = True
            try:
                await asyncio.to_thread(head_count_pipeline.process_frame, frame, sync_callback)
            except Exception as e:
                print(f"Error in head_count_pipeline.process_frame: {e}")
        else:
            await asyncio.sleep(0.1)

    async def _handle_ai_result(self, session_id: str, result: dict):
        """
        Process output from either AI pipeline and apply business logic.

        recognition events (from FaceRecognitionPipeline):
            >= 70% → auto-mark present (FACE method)
            30–69% → prompt fingerprint verification
            < 30%  → unknown, ignored

        head_count events (from HeadCountPipeline):
            → Update head count, broadcast comparison, update LCD
        """

        if result["type"] == "recognition":
            student_id = result["student_id"]
            confidence = result["confidence"]

            # Skip if already recognized this session (prevents duplicate DB writes)
            if session_manager.is_student_recognized(session_id, student_id):
                return

            if confidence >= ai_config.FACE_CONFIDENCE_AUTO:
                # >= 70% → auto-mark present
                await self._mark_attendance(
                    session_id=session_id,
                    student_id=student_id,
                    method=AttendanceMethod.FACE,
                    confidence=confidence
                )

            elif confidence >= ai_config.FACE_CONFIDENCE_FINGERPRINT:
                # 30%–69% → request fingerprint verification
                # Broadcast so the dashboard shows a prompt
                student_id_str = str(student_id)
                await session_manager.broadcast_event(session_id, "fingerprint_required", {
                    "student_id": student_id_str,
                    "confidence": confidence,
                    "message": f"Low confidence ({confidence*100:.0f}%). Please use fingerprint sensor."
                })

            else:
                # < 30% → unknown face, ignored
                await session_manager.broadcast_event(session_id, "unknown_face", {
                    "confidence": confidence
                })

        elif result["type"] == "unknown_face":
            # Face detected but no student embedding matches at all
            await session_manager.broadcast_event(session_id, "unknown_face", {
                "confidence": result.get("confidence", 0.0)
            })

        elif result["type"] == "head_count":
            count = result["count"]
            recognized_count = session_manager.get_recognized_count(session_id)

            # Update stored head count
            session_manager.set_head_count(session_id, count)

            # Persist to DB
            await self._update_session_head_count(session_id, count)

            is_match = (count == recognized_count)

            # Broadcast head count update to dashboard
            await session_manager.broadcast_event(session_id, "head_count_update", {
                "head_count": count,
                "present_count": recognized_count,
                "is_match": is_match,
            })

            # Broadcast LCD mirror event (lets dashboard replicate what LCD shows)
            if is_match:
                status_line = "Match"
            else:
                status_line = f"Mismatch ({count - recognized_count} extra)"

            await session_manager.broadcast_event(session_id, "lcd_update", {
                "line1": f"Present  = {recognized_count}",
                "line2": f"HeadCount= {count}",
                "line3": status_line,
                "line4": "Mode: HEAD COUNT",
            })

            # Update physical LCD
            self._lcd_show_headcount(recognized_count, count)

    async def _mark_attendance(
        self,
        session_id: str,
        student_id: UUID,
        method: AttendanceMethod,
        confidence: float
    ):
        """Write attendance record to DB and broadcast to dashboard + LCD."""

        async with async_session_factory() as db:
            # Fetch the attendance record for this student in this session
            stmt = select(Attendance).where(
                Attendance.session_id == UUID(session_id),
                Attendance.student_id == student_id
            )
            res = await db.execute(stmt)
            record = res.scalar_one_or_none()

            if record is None:
                # No pre-seeded record — create one on the fly (e.g., guest / late enrollment)
                record = Attendance(
                    session_id=UUID(session_id),
                    student_id=student_id,
                    status=AttendanceStatus.ABSENT,  # will be flipped to PRESENT below
                    method=method,                   # required NOT NULL field
                )
                db.add(record)
                await db.flush()  # assign DB-generated id before updating fields

            if record.status != AttendanceStatus.PRESENT:
                record.status = AttendanceStatus.PRESENT
                record.method = method
                record.confidence = confidence
                record.marked_at = datetime.now(timezone.utc)

                # Update recognized_count in the session record
                sess_stmt = select(AttendanceSession).where(
                    AttendanceSession.id == UUID(session_id)
                )
                sess_res = await db.execute(sess_stmt)
                session_rec = sess_res.scalar_one()
                session_rec.recognized_count += 1

                # Fetch student name for rich events (dashboard + LCD)
                stu_stmt = select(Student).where(Student.id == student_id)
                stu_res = await db.execute(stu_stmt)
                student = stu_res.scalar_one_or_none()
                student_name = student.full_name if student else str(student_id)[:8]

                await db.commit()

                # Update in-memory cache
                session_manager.mark_student_recognized(session_id, student_id)
                recognized_count = session_manager.get_recognized_count(session_id)

                # Broadcast attendance_marked with student name for dashboard
                await session_manager.broadcast_event(session_id, "attendance_marked", {
                    "student_id": str(student_id),
                    "student_name": student_name,
                    "method": method.value,
                    "confidence": confidence,
                })

                # Broadcast LCD mirror event
                await session_manager.broadcast_event(session_id, "lcd_update", {
                    "line1": f"Total Attendee:{recognized_count:3d}",
                    "line2": f"{student_name[:18]:18s}",
                    "line3": "   >> Present",
                    "line4": "Mode: ATTENDANCE",
                })

                # Update physical LCD
                self._lcd_show_attendance(recognized_count, student_name)

    async def _update_session_head_count(self, session_id: str, count: int):
        """Persist the latest head count to the AttendanceSession record."""
        async with async_session_factory() as db:
            stmt = select(AttendanceSession).where(
                AttendanceSession.id == UUID(session_id)
            )
            res = await db.execute(stmt)
            session_rec = res.scalar_one_or_none()
            if session_rec:
                session_rec.head_count = count
                await db.commit()

    # ── LCD helper methods ────────────────────────────────────────────────────

    def _lcd_show_idle(self):
        """Show idle/branding screen on the LCD."""
        try:
            if self.lcd:
                self.lcd.show_idle()
        except Exception as e:
            logging.error(f"LCD Error (idle): {e}")

    def _lcd_show_attendance(self, total_present: int, student_name: str):
        """Update LCD with latest attendance info."""
        try:
            if self.lcd:
                self.lcd.show_attendance_update(total_present, student_name)
        except Exception as e:
            logging.error(f"LCD Error (attendance): {e}")

    def _lcd_show_headcount(self, present_count: int, head_count: int):
        """Update LCD with head count comparison."""
        try:
            if self.lcd:
                self.lcd.show_headcount_result(present_count, head_count)
        except Exception:
            pass


engine = AttendanceEngine()
