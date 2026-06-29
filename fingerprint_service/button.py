import asyncio
from typing import Optional

from backend.config import settings
from fingerprint_service.sensor import fp_sensor
from attendance_engine.session_manager import session_manager
from models.attendance import AttendanceMethod
from sqlalchemy import select
from database.connection import async_session_factory
from models.fingerprint import FingerprintData

class HardwareButtonListener:
    def __init__(self):
        self.button = None
        self.loop = None

    def start(self, loop: asyncio.AbstractEventLoop):
        """Initialize the button listener. Fallback gracefully if not on Raspberry Pi."""
        self.loop = loop
        try:
            from gpiozero import Button
            self.button = Button(settings.BUTTON_GPIO_PIN, bounce_time=0.5)
            self.button.when_pressed = self._on_pressed
            print(f"Hardware button listener started on GPIO {settings.BUTTON_GPIO_PIN}")
        except Exception as e:
            print(f"Could not initialize hardware button (Mock mode or not on RPi): {e}")

    def stop(self):
        if self.button:
            self.button.close()

    def _on_pressed(self):
        """Synchronous callback triggered by gpiozero."""
        if not self.loop:
            return
        
        # Schedule the async flow on the main event loop
        asyncio.run_coroutine_threadsafe(self._handle_button_press(), self.loop)

    async def _handle_button_press(self):
        """Async handler to run fingerprint verification and mark attendance."""
        session_id = session_manager.get_active_session()
        if not session_id:
            print("Hardware Button: No active session to mark attendance.")
            return

        print("Hardware Button: Triggering fingerprint scan...")
        
        # Run verify_flow in a thread to avoid blocking the async loop
        # Since verify_flow does serial I/O and time.sleep, it's blocking
        success, match_id = await asyncio.to_thread(fp_sensor.verify_flow)
        
        if not success or match_id is None:
            print("Hardware Button: Scan failed or no match found.")
            return

        # Lookup student_id from database
        async with async_session_factory() as db:
            stmt = select(FingerprintData).where(FingerprintData.sensor_id == match_id)
            result = await db.execute(stmt)
            fp_data = result.scalar_one_or_none()
            
            if not fp_data:
                print(f"Hardware Button: Match found (ID {match_id}) but not in database.")
                return
            
            student_id = fp_data.student_id

        print(f"Hardware Button: Recognized student {student_id}. Marking attendance...")
        
        # Mark attendance using the engine
        # We import here to avoid circular imports if engine imports us
        from attendance_engine.engine import engine
        await engine._mark_attendance(
            session_id=session_id,
            student_id=student_id,
            method=AttendanceMethod.FINGERPRINT,
            confidence=1.0
        )

# Singleton instance
hardware_button_listener = HardwareButtonListener()
