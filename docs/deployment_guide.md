# ClassOS — Raspberry Pi 5 Deployment Guide

## Prerequisites

- Raspberry Pi 5 (8GB) with Raspberry Pi OS 64-bit (Bookworm)
- MicroSD card (32GB+ recommended)
- USB Webcam (UVC-compatible, 720p+, connected via USB)
- R307 Fingerprint Sensor (wired to GPIO — see [hardware_wiring.md](hardware_wiring.md))
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
git clone https://github.com/yourusername/ClassOS.git /opt/ClassOS
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
2. Verify USB webcam is detected
3. Enable UART for fingerprint sensor
4. Install Docker & Docker Compose
5. Download AI model weights (YOLOv8n)
6. Build and start all Docker services

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

### 4.2 Enable Hardware

```bash
# Verify USB webcam is connected
ls -la /dev/video*
lsusb  # should show your webcam

# Edit boot config (for UART / fingerprint sensor)
sudo nano /boot/firmware/config.txt

# Add these lines:
enable_uart=1
dtoverlay=uart0

# Disable serial console
sudo systemctl disable serial-getty@ttyS0.service

# Reboot
sudo reboot
```

### 4.3 Configure Environment

```bash
cd /opt/ClassOS
cp .env.example .env
nano .env

# Key settings to update:
# - Set CAMERA_DEVICE_INDEX=0 (or the index of your USB webcam)
# - Set FINGERPRINT_MOCK_MODE=false (use real sensor)
# - Change JWT_SECRET_KEY and SECRET_KEY to random strings
# - Change POSTGRES_PASSWORD
```

### 4.4 Build & Start

```bash
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
```

### Access Dashboard

Open a browser and navigate to:
```
http://<raspberry-pi-ip>
```

Login with default credentials:
- **Email**: admin@classos.local
- **Password**: changeme123

> ⚠️ **Change the default admin password immediately!**

---

## Step 6: Hardware Device Access (Docker)

For Docker to access the USB webcam and fingerprint sensor, uncomment these lines in `docker-compose.yml`:

```yaml
backend:
  devices:
    - /dev/video0:/dev/video0       # USB Webcam
    - /dev/ttyS0:/dev/ttyS0         # R307 UART
  privileged: true
```

Then restart:
```bash
docker compose down
docker compose up -d
```

---

## Maintenance

### View Logs
```bash
docker compose logs -f backend    # Backend logs
docker compose logs -f db          # Database logs
```

### Restart Services
```bash
docker compose restart backend
```

### Update ClassOS
```bash
cd /opt/ClassOS
git pull
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
| `CAMERA_FPS` | 30 | Most USB webcams support 30fps at 720p |
| `HEAD_COUNT_INTERVAL` | 5 | Run YOLO every 5th frame to save CPU |
| `DB_POOL_SIZE` | 5 | Adequate for single-classroom use |
| `YOLO_CONFIDENCE` | 0.5 | Balance between detection and false positives |
| Docker `--workers` | 1 | Single worker to avoid memory pressure |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Backend won't start | DB not ready | Check `docker compose logs db` |
| Camera feed black | Webcam not detected | Verify USB webcam with `lsusb`, check `/dev/video0` exists |
| Fingerprint timeout | UART not enabled | Verify `enable_uart=1`, check wiring |
| Slow recognition | CPU overloaded | Reduce `CAMERA_FPS`, increase `HEAD_COUNT_INTERVAL` |
| Out of memory | Too many models | Use `--workers 1`, reduce `DB_POOL_SIZE` |
