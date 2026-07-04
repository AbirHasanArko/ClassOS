"""
ClassOS — LCD Display Service
Drives a 20x4 I2C Character LCD (HD44780 + PCF8574 I2C backpack).

Hardware: Any 20x4 HD44780-compatible LCD with a PCF8574 I2C backpack module.
Default I2C address: 0x27 (run `i2cdetect -y 1` on the Pi to confirm).

Wiring:
    LCD Backpack VCC  → Raspberry Pi Pin 2 (5V)
    LCD Backpack GND  → Raspberry Pi Pin 6 (GND)
    LCD Backpack SDA  → Raspberry Pi Pin 3 (GPIO2 / SDA1)
    LCD Backpack SCL  → Raspberry Pi Pin 5 (GPIO3 / SCL1)

Custom Characters:
    The HD44780 has no Unicode support. We define custom CGRAM characters
    for a checkmark (✓) and a cross (✗) using 5x8 pixel bitmaps.

Fallback:
    If RPLCD or smbus2 are not installed, or if the hardware is not detected,
    the service falls back to console logging. No crashes, no exceptions propagate.
"""

import threading
import logging
import sys
from typing import Optional

from backend.config import settings

logger = logging.getLogger("classos.lcd")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)




# ─── Custom character bitmaps (5x8 pixels, HD44780 CGRAM format) ─────────────

# Checkmark ✓  (used for "Match" in head count mode)
CHAR_CHECKMARK = [
    0b00000,
    0b00000,
    0b00001,
    0b00011,
    0b10110,
    0b11100,
    0b01000,
    0b00000,
]

# Cross ✗  (used for "Mismatch" in head count mode)
CHAR_CROSS = [
    0b00000,
    0b10001,
    0b01010,
    0b00100,
    0b01010,
    0b10001,
    0b00000,
    0b00000,
]

# CGRAM slot indices (0–7 available on HD44780)
CGRAM_CHECKMARK = 0
CGRAM_CROSS = 1


class LCDDisplay:
    """
    Thread-safe 20×4 I2C LCD driver.

    Usage:
        lcd_display.show_attendance_update(15, "John Doe")
        lcd_display.show_headcount_result(15, 17)
        lcd_display.show_idle()
        lcd_display.clear()

    The display is divided into two modes:

    ATTENDANCE MODE (Take Attendance):
        Line 1: "Total Attendee: XX"
        Line 2: "<Student Name>      "
        Line 3: "   >> Present       "
        Line 4: "Mode: ATTENDANCE    "

    HEAD COUNT MODE (Verify Head Count):
        Line 1: "Present    =  XX    "
        Line 2: "Head Count =  XX    "
        Line 3: "[✓ Match / ✗ Mismatch]"
        Line 4: "Mode: HEAD COUNT    "

    IDLE:
        Line 1: "   ClassOS v2.0     "
        Line 2: "  AI Attendance Sys "
        Line 3: "                    "
        Line 4: "    Ready...        "
    """

    COLS = 20
    ROWS = 4

    def __init__(self):
        self._lock = threading.Lock()
        self._lcd = None
        self._enabled = False
        self._mock_mode = False  # Falls back to stdout if True

        if not settings.LCD_ENABLED:
            logger.info("LCD: Disabled via LCD_ENABLED=false")
            self._mock_mode = True
            return

        self._init_hardware()

    def _init_hardware(self):
        """Attempt to initialize the LCD hardware. Falls back to mock if unavailable."""
        try:
            from RPLCD.i2c import CharLCD
            import smbus2

            # Verify I2C bus is accessible
            bus = smbus2.SMBus(settings.LCD_I2C_BUS)
            bus.close()

            self._lcd = CharLCD(
                i2c_expander='PCF8574',
                address=settings.LCD_I2C_ADDRESS,
                port=settings.LCD_I2C_BUS,
                cols=self.COLS,
                rows=self.ROWS,
                dotsize=8,
                auto_linebreaks=False,
                backlight_enabled=True,
            )

            # Load custom characters into CGRAM
            self._lcd.create_char(CGRAM_CHECKMARK, CHAR_CHECKMARK)
            self._lcd.create_char(CGRAM_CROSS, CHAR_CROSS)

            self._enabled = True
            logger.info(f"✅ LCD: 20x4 I2C LCD initialized at address 0x{settings.LCD_I2C_ADDRESS:02X} on bus {settings.LCD_I2C_BUS}")

            # Show splash screen
            self.show_idle()

        except ImportError as e:
            logger.warning(f"⚠️  LCD: RPLCD or smbus2 not installed ({e}). Falling back to console mode.")
            self._mock_mode = True
        except Exception as e:
            logger.error(f"⚠️  LCD: Hardware not available ({e}). Falling back to console mode.")
            self._mock_mode = True

    def _write(self, line1: str = "", line2: str = "", line3: str = "", line4: str = ""):
        """
        Write four lines to the LCD. Each line is padded/truncated to 20 chars.
        Thread-safe via lock.
        """
        lines = [line1, line2, line3, line4]
        formatted = [f"{line:<20.20s}" for line in lines]

        if self._mock_mode:
            print(f"\n┌{'─'*20}┐")
            for line in formatted:
                print(f"│{line}│")
            print(f"└{'─'*20}┘")
            return

        if not self._enabled or self._lcd is None:
            return

        with self._lock:
            try:
                self._lcd.home()
                self._lcd.clear()
                # Write each line at its row position
                row_offsets = [0x00, 0x40, 0x14, 0x54]  # HD44780 20x4 row DDRAM addresses
                for i, line in enumerate(formatted):
                    self._lcd.cursor_pos = (i, 0)
                    self._lcd.write_string(line)
            except Exception as e:
                print(f"LCD write error: {e}")

    def show_idle(self):
        """Display idle/branding screen when no session is active."""
        self._write(
            line1="   ClassOS  v2.0    ",
            line2=" AI Attendance Sys  ",
            line3="                    ",
            line4="      Ready...      ",
        )

    def show_attendance_update(self, total_present: int, student_name: str):
        """
        Show real-time attendance update.

        Args:
            total_present: Total number of students marked present this session.
            student_name:  Full name of the student just marked present.
        """
        # Truncate student name to fit (20 chars max for display)
        name_short = student_name[:18]

        self._write(
            line1=f"Total Attendee:{total_present:3d} ",
            line2=f"{name_short:<18s}  ",
            line3="   >> Present       ",
            line4="Mode: ATTENDANCE    ",
        )

    def show_headcount_result(self, present_count: int, head_count: int):
        """
        Show head count comparison result.

        Args:
            present_count: Number of students marked present by face/fingerprint.
            head_count:    Number of heads counted by YOLOv8 on Camera 1.
        """
        is_match = present_count == head_count

        if is_match:
            # Use custom checkmark character (CGRAM slot 0)
            status = f"\x00 Match!             "
        else:
            diff = head_count - present_count
            # Use custom cross character (CGRAM slot 1)
            status = f"\x01 Mismatch({diff:+d})     "

        self._write(
            line1=f"Present    ={present_count:4d}    ",
            line2=f"Head Count ={head_count:4d}    ",
            line3=status,
            line4="Mode: HEAD COUNT    ",
        )

    def show_fingerprint_prompt(self, student_partial_name: str = ""):
        """
        Show fingerprint verification prompt on the LCD.
        Displayed when face confidence is between 30%–69%.
        """
        name_line = f"{student_partial_name[:20]:<20s}" if student_partial_name else "                    "
        self._write(
            line1="Fingerprint Needed! ",
            line2=name_line,
            line3="Place finger on     ",
            line4="sensor & scan...    ",
        )

    def clear(self):
        """Clear the LCD display."""
        if self._mock_mode:
            logger.info("LCD: [cleared]")
            return
        if self._enabled and self._lcd:
            with self._lock:
                try:
                    self._lcd.clear()
                except Exception:
                    pass


# Singleton instance
lcd_display = LCDDisplay()
