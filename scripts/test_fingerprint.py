"""
ClassOS — Fingerprint Sensor Hardware Test Script
Run with: python -m scripts.test_fingerprint
"""

import sys


def test_fingerprint():
    print("=" * 50)
    print("  ClassOS — Fingerprint Sensor Test")
    print("=" * 50)

    # 1. Import test
    print("\n[1/3] Importing fingerprint service...")
    try:
        from fingerprint_service.sensor import fp_sensor
        print("  ✅ Import successful")
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        sys.exit(1)

    # 2. Connection status
    print(f"\n[2/3] Checking sensor status...")
    print(f"  UART Port:  {fp_sensor.port}")
    print(f"  Baud Rate:  {fp_sensor.baudrate}")
    print(f"  Mock Mode:  {fp_sensor.mock_mode}")

    is_connected = fp_sensor.get_status()
    if is_connected:
        print(f"  ✅ Sensor is {'responding (mock)' if fp_sensor.mock_mode else 'connected and responsive'}")
    else:
        print("  ❌ Sensor not responding")
        print("  Hints:")
        print("    - Check TX↔RX wiring (cross-connect)")
        print("    - Verify enable_uart=1 in /boot/firmware/config.txt")
        print("    - Run: sudo systemctl disable serial-getty@ttyS0.service")
        sys.exit(1)

    # 3. Capture test (only in mock mode to avoid requiring a finger)
    print(f"\n[3/3] Testing image capture...")
    if fp_sensor.mock_mode:
        result = fp_sensor.capture_image()
        print(f"  ✅ Capture returned: {result} (mock mode)")
    else:
        print("  ⚠️  Skipping capture test in live mode (requires finger placement)")
        print("  To test enrollment, use: POST /api/fingerprint/enroll")

    print("\n" + "=" * 50)
    print("  Fingerprint sensor test PASSED ✅")
    print("=" * 50)


if __name__ == "__main__":
    test_fingerprint()
