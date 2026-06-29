# ClassOS — Hardware Wiring Guide

## Components

| Component | Model | Qty | Purpose |
|-----------|-------|-----|---------|
| Single Board Computer | Raspberry Pi 5 (8GB RAM) | 1 | Main edge server |
| Camera 0 (Entry) | Raspberry Pi Camera Module v2/v3 | 1 | Face recognition — connected to CAM/DISP 0 |
| Camera 1 (Classroom) | Raspberry Pi Camera Module v2/v3 | 1 | Head counting (YOLOv8) — connected to CAM/DISP 1 |
| Fingerprint Sensor | R307 Optical Fingerprint Module | 1 | Identity fallback verification (UART) |
| LCD Display | 20×4 HD44780 + I2C PCF8574 backpack | 1 | Real-time status display |
| Push Button | Generic Momentary Switch | 1 | Trigger direct fingerprint scan |
| Jumper Wires | Female-to-Female | 8+ | GPIO connections |

> 💡 **Fallback**: If only one camera is available, connect it to CAM/DISP 0. The system detects Camera 1 automatically and disables the "Verify Head Count" mode gracefully.

---

## 1. Raspberry Pi Camera Modules (CSI Connector)

The two cameras connect to the **two dedicated CSI (Camera Serial Interface) / DISP ports** on the Raspberry Pi 5 PCIe connector block.

### Camera Identification on Raspberry Pi OS (Bookworm)

On Raspberry Pi OS Bookworm with `libcamera`, the cameras appear as:

```
/dev/video0  → Camera 0 (CAM/DISP 0)  — Entry/Face Recognition camera
/dev/video2  → Camera 1 (CAM/DISP 1)  — Classroom/Head Count camera
```

> ⚠️ **Note**: Raspberry Pi Camera Modules on the CSI ports appear as `/dev/video0` and `/dev/video2` (not video1), because the ISP creates intermediate device nodes. Run `rpicam-hello --list-cameras` to verify.

### Verify cameras are detected:
```bash
# List all video devices
ls -la /dev/video*

# Verify camera list with libcamera
rpicam-hello --list-cameras

# Expected output on RPi5 with two cameras:
# Available cameras
# -----------------
# 0 : imx708 [4608x2592 10-bit RGGB] (/base/.../i2c@0/imx708@1a)
# 1 : imx708 [4608x2592 10-bit RGGB] (/base/.../i2c@0/imx708@1a)

# Test Camera 0 (entry)
python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, f = cap.read(); print('Camera 0 OK' if ret else 'FAILED'); cap.release()"

# Test Camera 1 (head count)
python3 -c "import cv2; cap = cv2.VideoCapture(2); ret, f = cap.read(); print('Camera 1 OK' if ret else 'FAILED'); cap.release()"
```

### Camera Positioning Recommendations

| Camera | Placement | Coverage | Purpose |
|--------|-----------|----------|---------|
| **Camera 0** | Near classroom entrance, eye level | Door area, 1–4 persons at a time | Face recognition when students enter |
| **Camera 1** | Ceiling mount at front/center of classroom | Entire classroom | Head count via YOLOv8 |

> 💡 **Camera 1 FOV**: For best head counting results, position Camera 1 at the front of the classroom pointing toward students, or overhead. A wide-angle lens (≥ 100°) is recommended for large classrooms.

### USB Webcam Alternative

If you prefer USB webcams instead of RPi Camera Modules:
1. Plug Camera 0 (entry) into any USB port → appears as `/dev/video0`
2. Plug Camera 1 (classroom) into another USB port → appears as `/dev/video1` or `/dev/video2`
3. Update `CAMERA_DEVICE_INDEX` and `CAMERA_1_DEVICE_INDEX` in `.env` to match

```bash
# Identify which USB webcam is which
v4l2-ctl --list-devices
```

---

## 2. R307 Fingerprint Sensor Wiring (UART)

The R307 communicates over **UART (serial)** at 57600 baud.

### Pin Connections:

```
R307 Sensor          Raspberry Pi 5
┌──────────┐         ┌──────────────┐
│ VCC (Red)├────────►│ Pin 1  (3.3V)│
│ GND (Blk)├────────►│ Pin 6  (GND) │
│ TX  (Yel)├────────►│ Pin 10 (RXD) │  ← GPIO15
│ RX  (Grn)├────────►│ Pin 8  (TXD) │  ← GPIO14
└──────────┘         └──────────────┘
```

> ⚠️ **Important**: The R307's TX connects to Pi's RX (GPIO15), and R307's RX connects to Pi's TX (GPIO14). This is a **cross-connection** — TX always connects to RX.

> ⚠️ **Voltage**: The R307 operates at **3.3V**. Do NOT connect VCC to the 5V pin.

### Enable UART:

```bash
sudo nano /boot/firmware/config.txt
```

Add these lines:
```
enable_uart=1
dtoverlay=uart0
```

Disable the serial console (it conflicts with UART):
```bash
sudo systemctl disable serial-getty@ttyS0.service
```

Reboot:
```bash
sudo reboot
```

### Test Fingerprint Sensor:

```bash
# Check if UART device exists
ls -la /dev/ttyS0

# Quick test with Python
python3 -c "
import serial
ser = serial.Serial('/dev/ttyS0', 57600, timeout=2)
print('UART port opened:', ser.is_open)
ser.close()
"
```

---

## 3. 20×4 I2C LCD Display Wiring

The 20×4 LCD uses the standard **HD44780** character display controller with a **PCF8574 I2C backpack** for easy 4-wire connection.

### I2C Pin Connections:

```
LCD I2C Backpack     Raspberry Pi 5
┌──────────────┐     ┌──────────────────┐
│ VCC (Red)    ├────►│ Pin 2 or 4 (5V)  │
│ GND (Black)  ├────►│ Pin 6, 9, 14 GND │
│ SDA (Blue)   ├────►│ Pin 3  (GPIO2)   │  ← SDA1
│ SCL (Yellow) ├────►│ Pin 5  (GPIO3)   │  ← SCL1
└──────────────┘     └──────────────────┘
```

> ⚠️ **Power**: The 20×4 LCD backlight requires **5V** to operate at full brightness. Use Pin 2 or Pin 4 (5V), NOT Pin 1 (3.3V).

> 💡 **I2C Address**: Most PCF8574 I2C backpacks default to **0x27**. Some use **0x3F**. Run `i2cdetect -y 1` to discover your module's address and update `LCD_I2C_ADDRESS` in `.env`.

### GPIO Pinout Reference:

```
                    ┌───────────┐
            3.3V  ●│ 1       2 │● 5V     ◄── LCD VCC
           GPIO2  ●│ 3       4 │● 5V
           GPIO3  ●│ 5       6 │● GND    ◄── LCD GND & R307 GND
           GPIO4  ●│ 7       8 │● GPIO14 (TXD) ◄── R307 RX
             GND  ●│ 9      10 │● GPIO15 (RXD) ◄── R307 TX
          GPIO17  ●│ 11     12 │● GPIO18
          GPIO27  ●│ 13     14 │● GND
          GPIO22  ●│ 15     16 │● GPIO23
            3.3V  ●│ 17     18 │● GPIO24
          GPIO10  ●│ 19     20 │● GND
           GPIO9  ●│ 21     22 │● GPIO25
          GPIO11  ●│ 23     24 │● GPIO8
             GND  ●│ 25     26 │● GPIO7
           GPIO0  ●│ 27     28 │● GPIO1
           GPIO5  ●│ 29     30 │● GND
           GPIO6  ●│ 31     32 │● GPIO12
          GPIO13  ●│ 33     34 │● GND
          GPIO19  ●│ 35     36 │● GPIO16
          GPIO26  ●│ 37     38 │● GPIO20
             GND  ●│ 39     40 │● GPIO21
                    └───────────┘

SDA (LCD) ──► Pin 3  (GPIO2)
SCL (LCD) ──► Pin 5  (GPIO3)
```

### Enable I2C:

```bash
# Enable I2C via raspi-config
sudo raspi-config
# → Interface Options → I2C → Enable

# OR manually in /boot/firmware/config.txt:
sudo nano /boot/firmware/config.txt
# Add:
dtparam=i2c_arm=on

sudo reboot
```

### Test I2C LCD:

```bash
# Install i2c-tools
sudo apt-get install -y i2c-tools

# Scan I2C bus — should show 0x27 (or 0x3F)
sudo i2cdetect -y 1

# Expected output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 20: -- -- -- -- -- -- -- 27 -- -- -- -- -- -- -- --

# Test from Python
python3 -c "
from RPLCD.i2c import CharLCD
lcd = CharLCD('PCF8574', 0x27, port=1, cols=20, rows=4)
lcd.write_string('ClassOS LCD OK!')
"
```

## 4. Momentary Push Button Wiring

The push button allows students to manually trigger the fingerprint scanner without needing to use the web dashboard.

### Pin Connections:

```
Momentary Button     Raspberry Pi 5
┌──────────────┐     ┌──────────────────┐
│ Leg 1        ├────►│ Pin 16 (GPIO23)  │
│ Leg 2        ├────►│ Pin 14 (GND)     │
└──────────────┘     └──────────────────┘
```

> 💡 **Pull-up Resistor**: The `gpiozero` library automatically enables the internal pull-up resistor on GPIO23, so you do not need any external resistors. Simply connect the button directly between GPIO23 and GND.

---

## 5. Complete Wiring Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5                             │
│                                                               │
│  CSI Port 0 (CAM 0)──── Flat Ribbon Cable ──► 📷 Camera 0   │
│                                               (Entry Door)    │
│  CSI Port 1 (CAM 1)──── Flat Ribbon Cable ──► 📷 Camera 1   │
│                                          (Classroom Ceiling)  │
│                                                               │
│  GPIO Header                                                  │
│  Pin 1  (3.3V) ──────────────────────────────► R307 VCC      │
│  Pin 2  (5V)   ──────────────────────────────► LCD VCC       │
│  Pin 3  (SDA1) ──────────────────────────────► LCD SDA       │
│  Pin 5  (SCL1) ──────────────────────────────► LCD SCL       │
│  Pin 6  (GND)  ──────────────────────────────► R307 GND      │
│                                                LCD GND        │
│  Pin 8  (TXD)  ──────────────────────────────► R307 RX       │
│  Pin 10 (RXD)  ──────────────────────────────► R307 TX       │
│  Pin 14 (GND)  ──────────────────────────────► Button GND    │
│  Pin 16 (GPIO23)─────────────────────────────► Button Leg 1  │
│                                                               │
│  Docker Engine (PostgreSQL + FastAPI + Nginx + React)         │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera 0 not detected | Run `rpicam-hello --list-cameras`, check CSI cable at both ends |
| Camera 1 not detected | Check second CSI/DISP port; run `ls /dev/video*` to see available devices |
| `/dev/video0` missing | Ensure RPi camera is enabled: `sudo raspi-config` → Interface → Camera |
| `CAMERA_1_DEVICE_INDEX` wrong | Try values 2, 4 (libcamera creates multiple nodes); check with `v4l2-ctl --list-devices` |
| R307 not responding | Check TX↔RX cross-wiring, verify baud rate 57600, ensure UART enabled |
| UART permission denied | Add user to dialout group: `sudo usermod -aG dialout $USER` |
| LCD not detected | Run `i2cdetect -y 1`; if no device shown, check SDA/SCL wiring and 5V power |
| LCD shows `0x3F` address | Update `LCD_I2C_ADDRESS=0x3F` in `.env` |
| LCD shows garbage characters | Check power supply (5V required), check I2C pull-up resistors |
| I2C permission denied | Add user to i2c group: `sudo usermod -aG i2c $USER` |
| Docker can't access cameras | Uncomment `devices:` lines in `docker-compose.yml` and set `privileged: true` |
| Docker can't access I2C | Add `/dev/i2c-1:/dev/i2c-1` to `devices:` in `docker-compose.yml` |
