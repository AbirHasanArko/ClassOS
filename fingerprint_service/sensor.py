import time
import serial
from typing import Tuple, Optional

from backend.config import settings

# R307 Command Packets (simplified)
FINGERPRINT_HEADER = bytes([0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF])

class FingerprintSensor:
    def __init__(self):
        self.port = settings.FINGERPRINT_UART_PORT
        self.baudrate = settings.FINGERPRINT_BAUD_RATE
        self.mock_mode = settings.FINGERPRINT_MOCK_MODE
        
        self.ser = None
        
        if not self.mock_mode:
            try:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            except Exception as e:
                print(f"Warning: Could not connect to R307 sensor: {e}")
                print("Falling back to mock mode.")
                self.mock_mode = True

    def _send_command(self, cmd: bytes) -> bytes:
        if self.mock_mode:
            time.sleep(0.5)
            # Mock success response: 0x00 is success code
            return FINGERPRINT_HEADER + bytes([0x07, 0x00, 0x03, 0x00, 0x00, 0x0A])
            
        if self.ser:
            self.ser.write(FINGERPRINT_HEADER + cmd)
            # Read header
            resp_header = self.ser.read(9)
            if len(resp_header) < 9:
                print(f"R307 error: incomplete header received ({len(resp_header)} bytes)")
                return b""
            # Read length
            length = (resp_header[7] << 8) | resp_header[8]
            # Read rest
            resp_data = self.ser.read(length)
            return resp_header + resp_data
        return b""

    def get_status(self) -> bool:
        """Check if sensor is responsive."""
        if self.mock_mode:
            return True
            
        # Command 0x01 (Handshake/Verify Password) is usually a safe ping
        # Let's mock a simple check for now
        return self.ser is not None and self.ser.is_open

    def capture_image(self) -> bool:
        """Tell sensor to capture a fingerprint image."""
        if self.mock_mode:
            return True
            
        # Cmd 0x01: GenImg
        # length 0x03, instr 0x01, checksum 0x00 0x05
        cmd = bytes([0x01, 0x00, 0x03, 0x01, 0x00, 0x05])
        resp = self._send_command(cmd)
        
        # Check confirmation code (byte 9)
        if len(resp) >= 10:
            if resp[9] == 0x00:
                return True
            # resp[9] == 0x02 means no finger, which is normal during polling
            if resp[9] != 0x02:
                print(f"R307 GenImg unexpected code: {hex(resp[9])}")
        return False

    def generate_template(self, buffer_id: int) -> bool:
        """Generate a character file from the image in CharBuffer1 or 2."""
        if self.mock_mode:
            return True
            
        # Cmd 0x02: Img2Tz
        chk = (0x01 + 0x00 + 0x04 + 0x02 + buffer_id)
        cmd = bytes([0x01, 0x00, 0x04, 0x02, buffer_id, (chk >> 8) & 0xFF, chk & 0xFF])
        resp = self._send_command(cmd)
        
        return len(resp) >= 10 and resp[9] == 0x00

    def create_model(self) -> bool:
        """Combine templates in Buffer1 and Buffer2 to create a model."""
        if self.mock_mode:
            return True
            
        # Cmd 0x05: RegModel
        cmd = bytes([0x01, 0x00, 0x03, 0x05, 0x00, 0x09])
        resp = self._send_command(cmd)
        
        return len(resp) >= 10 and resp[9] == 0x00

    def store_model(self, location_id: int) -> bool:
        """Store the combined model from Buffer1/2 into flash memory at location_id."""
        if self.mock_mode:
            return True
            
        # Cmd 0x06: Store
        buffer_id = 0x01 # Usually store from buffer 1
        chk = (0x01 + 0x00 + 0x06 + 0x06 + buffer_id + (location_id >> 8) + (location_id & 0xFF))
        cmd = bytes([0x01, 0x00, 0x06, 0x06, buffer_id, (location_id >> 8) & 0xFF, location_id & 0xFF, (chk >> 8) & 0xFF, chk & 0xFF])
        resp = self._send_command(cmd)
        
        return len(resp) >= 10 and resp[9] == 0x00

    def search_fingerprint(self) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Search for the fingerprint (currently in Buffer1) against all stored models.
        Returns: (success, match_location_id, match_score)
        """
        if self.mock_mode:
            # Mock returning sensor ID 1 with high score
            return True, 1, 95
            
        # Cmd 0x04: Search
        # Search Buffer 1, Start Page 0, End Page 200
        buffer_id = 0x01
        start_page = 0
        page_num = 200
        
        chk = 0x01 + 0x00 + 0x08 + 0x04 + buffer_id + (start_page >> 8) + (start_page & 0xFF) + (page_num >> 8) + (page_num & 0xFF)
        cmd = bytes([
            0x01, 0x00, 0x08, 0x04, buffer_id, 
            (start_page >> 8) & 0xFF, start_page & 0xFF, 
            (page_num >> 8) & 0xFF, page_num & 0xFF,
            (chk >> 8) & 0xFF, chk & 0xFF
        ])
        
        resp = self._send_command(cmd)
        
        # Success response is 16 bytes total:
        # 9 bytes header + 7 bytes data (1 byte CC, 2 bytes ID, 2 bytes Score, 2 bytes Checksum)
        if len(resp) >= 14 and resp[9] == 0x00:
            match_id = (resp[10] << 8) | resp[11]
            score = (resp[12] << 8) | resp[13]
            return True, match_id, score
            
        return False, None, None

    def _wait_for_image(self, timeout: int = 15) -> bool:
        """Poll the sensor until an image is captured or timeout is reached."""
        if self.mock_mode:
            time.sleep(1) # simulate user interaction
            return True
            
        start = time.time()
        while time.time() - start < timeout:
            if self.capture_image():
                return True
            time.sleep(0.2)
        return False

    def enroll_flow(self, location_id: int) -> bool:
        """Complete workflow to enroll a finger. Requires two placements."""
        print("Please place finger on sensor...")
        # Step 1: GenImg
        if not self._wait_for_image(): return False
        # Step 2: Img2Tz (Buffer 1)
        if not self.generate_template(1): return False
        
        print("Please lift and place same finger again...")
        time.sleep(2) # Wait for finger to lift
        
        # Step 3: GenImg
        if not self._wait_for_image(): return False
        # Step 4: Img2Tz (Buffer 2)
        if not self.generate_template(2): return False
        
        # Step 5: RegModel
        if not self.create_model(): return False
        # Step 6: Store
        if not self.store_model(location_id): return False
        
        print(f"Enrolled successfully at ID {location_id}")
        return True

    def verify_flow(self) -> Tuple[bool, Optional[int]]:
        """Complete workflow to read finger and return matching ID."""
        if not self._wait_for_image(): return False, None
        if not self.generate_template(1): return False, None
        
        success, match_id, score = self.search_fingerprint()
        if success and match_id is not None:
            print(f"Matched ID {match_id} with score {score}")
            return True, match_id
            
        return False, None

# Singleton instance
fp_sensor = FingerprintSensor()
