import asyncio
from typing import Optional

from backend.config import settings
from fingerprint_service.sensor import fp_sensor
from attendance_engine.session_manager import session_manager
from models.attendance import AttendanceMethod
from sqlalchemy import select
from database.connection import async_session_factory
from models.fingerprint import FingerprintData
import logging

logger = logging.getLogger("classos.button")


class HardwareButtonListener:
    """
    Listens for a physical momentary push button on a GPIO pin.

    Uses the `lgpio` library directly (instead of `gpiozero`) to ensure the
    RP1 chip's internal pull-up resistor is explicitly activated via
    `lgpio.gpio_claim_input(h, pin, lgpio.SET_PULL_UP)`.

    Background: On the Raspberry Pi 5, `gpiozero`'s fallback pin factory
    can fail to configure the internal pull-up resistor on the RP1 chip,
    leaving the GPIO pin in a "floating" state. This causes CMOS
    shoot-through current inside the RP1 silicon, drawing hundreds of mA
    of phantom power and triggering low-voltage warnings/shutdowns — even
    though the CPU is idle and the button works correctly.

    By using `lgpio` directly, we bypass gpiozero's abstraction and
    explicitly command the RP1 hardware to enable its pull-up.
    """

    def __init__(self):
        self._gpio_handle = None   # lgpio chip handle
        self._gpio_pin = None      # GPIO pin number
        self.loop = None
        self._running = False

    def start(self, loop: asyncio.AbstractEventLoop):
        """Initialize the button listener using direct lgpio calls."""
        self.loop = loop
        self._running = True
        self._gpio_pin = settings.BUTTON_GPIO_PIN

        try:
            import lgpio

            # Open the RP1 GPIO chip (gpiochip0 on modern Pi 5 kernels,
            # falls back to gpiochip4 on older kernels)
            for chip_num in (0, 4):
                try:
                    self._gpio_handle = lgpio.gpiochip_open(chip_num)
                    logger.info(f"Opened gpiochip{chip_num} successfully")
                    break
                except Exception:
                    continue

            if self._gpio_handle is None:
                raise RuntimeError("Could not open any gpiochip (tried 0 and 4)")

            # Explicitly claim the pin as INPUT with PULL-UP enabled.
            # This is the critical line that fixes the low-voltage issue:
            # it forces the RP1 hardware to activate its internal pull-up
            # resistor, preventing the pin from floating.
            lgpio.gpio_claim_input(self._gpio_handle, self._gpio_pin, lgpio.SET_PULL_UP)

            # Start our async polling loop (10Hz, near-zero CPU usage)
            self.loop.create_task(self._poll_button())

            logger.info(
                f"Hardware button listener started on GPIO{self._gpio_pin} "
                f"(Direct lgpio — pull-up explicitly enabled)"
            )
        except Exception as e:
            logger.error(f"Could not initialize hardware button: {e}")
            self._running = False

    def stop(self):
        self._running = False
        if self._gpio_handle is not None:
            try:
                import lgpio
                lgpio.gpio_free(self._gpio_handle, self._gpio_pin)
                lgpio.gpiochip_close(self._gpio_handle)
            except Exception:
                pass
            self._gpio_handle = None

    async def _poll_button(self):
        """Ultra-low CPU polling loop using lgpio.gpio_read()."""
        import lgpio

        while self._running:
            try:
                if self._gpio_handle is not None:
                    # gpio_read returns 0 when the button is pressed
                    # (pulled to GND) and 1 when released (pulled up to 3.3V)
                    level = lgpio.gpio_read(self._gpio_handle, self._gpio_pin)
                    if level == 0:  # Button is pressed (active low)
                        await self._handle_button_press()
                        # Debounce: wait 2 seconds before checking again
                        await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Button polling error: {e}")

            # Sleep 100ms between checks (10Hz poll rate)
            await asyncio.sleep(0.1)

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
