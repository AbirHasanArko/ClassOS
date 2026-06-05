# ClassOS — Hardware Wiring Guide

## Components

| Component | Model | Qty |
|-----------|-------|-----|
| Single Board Computer | Raspberry Pi 5 (8GB RAM) | 1 |
| Camera | USB Webcam (UVC-compatible, 720p+) | 1 |
| Fingerprint Sensor | R307 Optical Fingerprint Module | 1 |
| Jumper Wires | Female-to-Female | 4 |

---

## 1. USB Webcam Connection

Any standard **UVC (USB Video Class)** compatible webcam will work. Most modern USB webcams are UVC-compatible out of the box — no drivers needed on Linux.

### Steps:
1. **Plug** the USB webcam into any available **USB port** on the Raspberry Pi 5
2. The webcam will appear as `/dev/video0` (or `/dev/video1` if another video device exists)
3. No reboot or config changes are required

> 💡 **Tip**: For best results, use a webcam that supports at least **720p @ 30fps**. Wide-angle lenses are recommended for classroom coverage.

### Test Webcam:
```bash
# Verify the device is detected
ls -la /dev/video*

# Quick test with v4l2
v4l2-ctl --list-devices

# Or with Python + OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, f = cap.read(); print('Camera OK' if ret else 'FAILED'); cap.release()"
```

---

## 2. R307 Fingerprint Sensor Wiring

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

### GPIO Pinout Reference:

```
                    ┌───────────┐
            3.3V  ●│ 1       2 │● 5V
           GPIO2  ●│ 3       4 │● 5V
           GPIO3  ●│ 5       6 │● GND  ◄── R307 GND
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

## 3. Complete Setup Photo Reference

```
┌──────────────────────────────────────────────┐
│              Raspberry Pi 5                   │
│                                               │
│    ┌──────────┐                               │
│    │ USB      │◄── USB Cable ──► 📷           │
│    │ Port     │                  USB Webcam    │
│    └──────────┘                               │
│                                               │
│    GPIO Header                                │
│    ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐                    │
│    │1│ │ │ │ │6│ │8│ │10│ ◄── R307 Wires     │
│    └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘                    │
│    3V  ...  GND  TXD  RXD                     │
│     │        │    │    │                       │
│     ▼        ▼    ▼    ▼                       │
│   ┌────────────────────────┐                  │
│   │    R307 Fingerprint    │                  │
│   │    Sensor Module       │                  │
│   │    ┌──────────────┐    │                  │
│   │    │  ◯  Scanning  │    │                  │
│   │    │     Window    │    │                  │
│   │    └──────────────┘    │                  │
│   └────────────────────────┘                  │
└──────────────────────────────────────────────┘
```

---

## 4. Troubleshooting

| Issue | Solution |
|-------|----------|
| Webcam not detected | Unplug and re-plug USB cable, run `lsusb` to verify, try a different USB port |
| `/dev/video0` missing | Check `ls /dev/video*`; if using another device, update `CAMERA_DEVICE_INDEX` in `.env` |
| R307 not responding | Check TX↔RX cross-wiring, verify baud rate 57600 |
| UART permission denied | Add user to dialout group: `sudo usermod -aG dialout $USER` |
| 3.3V not enough power | Some R307 clones need 5V — check your module's datasheet |
| Camera shows black frames | Check lighting, verify webcam works with `v4l2-ctl --list-devices` |

