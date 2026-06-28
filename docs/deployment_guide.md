# ClassOS — Raspberry Pi 5 Deployment Guide

## Prerequisites

- Raspberry Pi 5 (8GB) with Raspberry Pi OS 64-bit (Bookworm)
- MicroSD card (32GB+ recommended)
- **2× Raspberry Pi Camera Module v2 or v3** (or UVC USB webcams)
  - Camera 0: Connected to CAM/DISP 0 (entry / face recognition)
  - Camera 1: Connected to CAM/DISP 1 (classroom overhead / head counting)
- R307 Fingerprint Sensor (wired to GPIO UART — see [hardware_wiring.md](hardware_wiring.md))
- 20×4 I2C LCD Display (PCF8574 backpack — see [hardware_wiring.md](hardware_wiring.md))
- Ethernet or WiFi connection
- SSH access enabled

---

## Step 1: Flash Raspberry Pi OS

1. Download **Raspberry Pi Imager** from [raspberrypi.com](https://www.raspberrypi.com/software/)
2. Select **Raspberry Pi OS (64-bit)** — Lite or Desktop
3. Flash to your microSD card
4. Before ejecting, configure WiFi and enable SSH in Imager settings

---

## Step 2: Initial System Setup

```bash
# Connect via SSH
ssh pi@<your-pi-ip>

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Git
sudo apt-get install -y git

# Clone ClassOS
git clone https://github.com/AbirHasanArko/ClassOS.git /opt/ClassOS
cd /opt/ClassOS
```

---

## Step 3: Automated Deployment

The easiest way to deploy is using the provided script:

```bash
chmod +x scripts/deploy_pi.sh
./scripts/deploy_pi.sh
```

This script will:
1. Update system packages
2. Enable I2C (for LCD display)
3. Enable UART (for fingerprint sensor)
4. Verify cameras are detected
5. Install Docker & Docker Compose
6. Download AI model weights (YOLOv8n)
7. Build and start all Docker services

---

## Step 4: Manual Deployment (Alternative)

If you prefer manual steps:

### 4.1 Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in
```

### 4.2 Enable Hardware Interfaces

```bash
# Enable Camera, I2C, and UART via raspi-config
sudo raspi-config
# → Interface Options → Camera → Enable
# → Interface Options → I2C → Enable
# → Interface Options → Serial Port → Disable shell, Enable hardware

# OR manually via /boot/firmware/config.txt:
sudo nano /boot/firmware/config.txt
```

Add / verify these lines in `/boot/firmware/config.txt`:
```
# Enable UART for R307 fingerprint sensor
enable_uart=1
dtoverlay=uart0

# Enable I2C for LCD display
dtparam=i2c_arm=on

# Camera support is auto-detected on RPi5 Bookworm
```

Disable the serial console (conflicts with UART):
```bash
sudo systemctl disable serial-getty@ttyS0.service
```

Add your user to required groups:
```bash
sudo usermod -aG i2c $USER
sudo usermod -aG dialout $USER
```

Reboot:
```bash
sudo reboot
```

### 4.3 Verify Hardware

```bash
# ----- Cameras -----
# Check available video devices
ls -la /dev/video*
rpicam-hello --list-cameras

# Test Camera 0 (entry / face recognition)
python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, f = cap.read(); print('Camera 0 OK' if ret else 'Camera 0 FAILED'); cap.release()"

# Test Camera 1 (head count)
python3 -c "import cv2; cap = cv2.VideoCapture(2); ret, f = cap.read(); print('Camera 1 OK' if ret else 'Camera 1 FAILED — will fall back to single-camera mode'); cap.release()"

# ----- LCD -----
# Verify I2C device detected
sudo i2cdetect -y 1
# Should show 27 (or 3F) in the output grid

# ----- Fingerprint Sensor -----
ls -la /dev/ttyS0
```

### 4.4 Configure Environment

```bash
cd /opt/ClassOS
cp .env.example .env
nano .env
```

Key settings to review:
```bash
# Camera indices — verify with `ls /dev/video*`
CAMERA_DEVICE_INDEX=0         # Camera 0 (entry/face) — CSI cam = /dev/video0
CAMERA_1_DEVICE_INDEX=2       # Camera 1 (head count) — CSI cam 1 = /dev/video2

# USB Webcam Fallback
# Comma-separated device indices to try if the preferred camera can't be opened.
# The system probes them in order and uses the first that opens.
# Example: single USB webcam on /dev/video1
# CAMERA_USB_FALLBACK_INDICES=1
# Example: try /dev/video1, then /dev/video3
# CAMERA_USB_FALLBACK_INDICES=1,3,4
CAMERA_USB_FALLBACK_INDICES=1,3,4

# Fingerprint sensor
FINGERPRINT_MOCK_MODE=false   # Set false for real hardware

# LCD display
LCD_ENABLED=true
LCD_I2C_ADDRESS=0x27          # Run i2cdetect to confirm

# AI thresholds
FACE_CONFIDENCE_AUTO=0.70     # >= 70% = auto present
FACE_CONFIDENCE_FINGERPRINT=0.30  # 30-69% = fingerprint required

# Secrets (CHANGE THESE!)
JWT_SECRET_KEY=<random-64-char-string>
SECRET_KEY=<random-64-char-string>
POSTGRES_PASSWORD=<strong-password>
```

### 4.5 Enable Hardware Device Access in Docker

Edit `docker-compose.yml` and **uncomment** the `devices` section under `backend`:

```yaml
backend:
  devices:
    - /dev/video0:/dev/video0       # Camera 0 — entry camera (face recognition)
    - /dev/video2:/dev/video2       # Camera 1 — overhead camera (head counting)
    - /dev/ttyS0:/dev/ttyS0         # R307 fingerprint sensor (UART)
    - /dev/i2c-1:/dev/i2c-1         # I2C bus for 20x4 LCD display
  privileged: true
```

> 💡 **USB Webcam Fallback**: If you're using a USB webcam instead of a CSI Camera Module, add its device node to the `devices` list too. For example, if your USB webcam is `/dev/video1`, add `- /dev/video1:/dev/video1`. The system will automatically use it as a fallback when `CAMERA_USB_FALLBACK_INDICES=1` is set in `.env`. There is no need to change any Python source code.

### 4.6 Build & Start

```bash
# Generate local SSL certificates
chmod +x scripts/generate_ssl.sh
./scripts/generate_ssl.sh

# Build and start all services
docker compose up -d --build

# Watch logs
docker compose logs -f

# Verify all services are running
docker compose ps
```

---

## Step 5: Verify Deployment

### Check Services

```bash
# All services should show "Up"
docker compose ps

# Expected output:
# classos-db        running   0.0.0.0:5432->5432
# classos-backend   running   0.0.0.0:8000->8000
# classos-frontend  running   80/tcp
# classos-nginx     running   0.0.0.0:80->80
```

### Test Endpoints

```bash
# Health check
curl http://localhost/api/health

# Should return:
# {"status":"healthy","app":"ClassOS","version":"1.0.0","environment":"production"}

# Test camera stream
curl -I http://localhost/api/stream/live        # Camera 0 stream
curl -I http://localhost/api/stream/headcount   # Camera 1 stream
```

### Access Dashboard

Open a browser and navigate to:
```
https://<raspberry-pi-ip>
```

Login with default credentials:
- **Email**: admin@classos.local
- **Password**: changeme123

> ⚠️ **Change the default admin password immediately!**

### Verify LCD

After the backend starts, the LCD should show the ClassOS idle screen:
```
   ClassOS  v2.0
 AI Attendance Sys
                   
      Ready...
```

If the LCD shows nothing:
- Check `docker compose logs backend | grep LCD`
- Run `i2cdetect -y 1` to confirm the module is detected

---

## Step 6: Hardware Device Access (Docker Reference)

For Docker to access hardware, these device mappings are needed:

| Device | Purpose | Docker mapping |
|--------|---------|----------------|
| `/dev/video0` | Camera 0 — face recognition | `- /dev/video0:/dev/video0` |
| `/dev/video2` | Camera 1 — head counting | `- /dev/video2:/dev/video2` |
| `/dev/ttyS0` | R307 fingerprint sensor | `- /dev/ttyS0:/dev/ttyS0` |
| `/dev/i2c-1` | I2C LCD display | `- /dev/i2c-1:/dev/i2c-1` |

---

## Maintenance

### View Logs
```bash
docker compose logs -f backend    # Backend logs (includes LCD, camera, AI events)
docker compose logs -f db          # Database logs
```

### Restart Services
```bash
docker compose restart backend
```

### Safe Update Process
When pulling new code from GitHub, back up your database first:
```bash
cd /opt/ClassOS

# 1. Take a backup of the current database
docker exec classos-db pg_dump -U classos classos_db > backup_$(date +%Y%m%d).sql

# 2. Pull the latest code
git pull

# 3. Rebuild and restart services
docker compose up -d --build
```

### Backup Database
```bash
docker exec classos-db pg_dump -U classos classos_db > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
cat backup.sql | docker exec -i classos-db psql -U classos classos_db
```

---

## Performance Optimization

The Pi 5 with 8GB RAM can handle ClassOS comfortably. Recommended optimizations:

| Setting | Value | Reason |
|---------|-------|--------|
| `CAMERA_FPS` | 30 | RPi Camera Modules support 30fps at 720p |
| `HEAD_COUNT_INTERVAL` | 5 | Run YOLO every 5th frame to save CPU |
| `DB_POOL_SIZE` | 5 | Adequate for single-classroom use |
| `YOLO_CONFIDENCE` | 0.5 | Balance between detection and false positives |
| Docker `--workers` | 1 | Single worker to avoid memory pressure |
| `FACE_CONFIDENCE_AUTO` | 0.70 | 70% = good balance; lower = more auto-marks |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Backend won't start | DB not ready | Check `docker compose logs db` |
| Camera 0 feed black | Camera 0 not detected | Verify CSI cable, run `rpicam-hello --list-cameras`; or set `CAMERA_USB_FALLBACK_INDICES=1` if using a USB webcam |
| Camera 0 fell back to USB webcam | CSI camera not detected | Expected behavior. Log shows `⚠️ Fell back to /dev/videoN`. Verify CSI cable or accept USB fallback. |
| Camera 1 feed missing | Camera 1 not connected | The "Verify Head Count" button will be disabled — this is expected fallback behavior |
| Camera 1 fell back to USB webcam | CSI camera 1 not detected | Expected. Ensure USB webcam is in `devices` in `docker-compose.yml` and its index is in `CAMERA_USB_FALLBACK_INDICES` |
| LCD shows nothing | I2C not detected | Run `i2cdetect -y 1`; check wiring and I2C enabled in raspi-config |
| LCD shows wrong address | PCF8574 variant | Try `LCD_I2C_ADDRESS=0x3F` in `.env` |
| Fingerprint timeout | UART not enabled | Verify `enable_uart=1`, check wiring, check `ls /dev/ttyS0` |
| Slow recognition | CPU overloaded | Reduce `CAMERA_FPS`, increase `HEAD_COUNT_INTERVAL` |
| Out of memory | Too many models | Use `--workers 1`, reduce `DB_POOL_SIZE` |
| Head count mode disabled | Camera 1 unavailable | System gracefully disables "Verify Head Count" — connect Camera 1 to CAM/DISP 1 or a second USB webcam |
| Gallery face upload fails | EXIF orientation issue (fixed in v2.1) | Ensure you are running v2.1+. The backend now auto-corrects portrait-mode phone photos. |
