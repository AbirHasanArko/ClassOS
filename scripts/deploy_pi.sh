#!/bin/bash
# =============================================================
# ClassOS — Raspberry Pi 5 Deployment Script
# Run this on a fresh Raspberry Pi OS 64-bit installation
# =============================================================

set -e

echo "========================================="
echo "  ClassOS — Raspberry Pi 5 Deployment"
echo "========================================="

# 1. System Updates
echo "[1/7] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Verify USB Webcam
echo "[2/7] Checking for USB webcam..."
if ls /dev/video* 1>/dev/null 2>&1; then
    echo "USB webcam detected: $(ls /dev/video*)"
else
    echo "Warning: No USB webcam detected at /dev/video*. Plug in a USB webcam before starting."
fi

# 3. Enable UART for R307 Fingerprint Sensor
echo "[3/7] Enabling UART for fingerprint sensor..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
    echo "dtoverlay=uart0" | sudo tee -a /boot/firmware/config.txt
fi

# Disable serial console (conflicts with UART)
sudo systemctl disable serial-getty@ttyS0.service 2>/dev/null || true

# 4. Install Docker
echo "[4/7] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed. You may need to log out and back in for group changes."
else
    echo "Docker already installed."
fi

# Install Docker Compose plugin
echo "Installing Docker Compose..."
sudo apt-get install -y docker-compose-plugin 2>/dev/null || \
    sudo pip3 install docker-compose

# 5. Clone and Configure
echo "[5/7] Setting up ClassOS..."
cd /opt
if [ ! -d "ClassOS" ]; then
    echo "Please clone the ClassOS repository to /opt/ClassOS"
    echo "  git clone https://github.com/yourusername/ClassOS.git /opt/ClassOS"
    exit 1
fi
cd ClassOS

# Create .env from template if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file. Please edit it with your settings:"
    echo "  nano /opt/ClassOS/.env"
fi

# 6. Download AI Model Weights
echo "[6/7] Downloading AI model weights..."
mkdir -p models

# YOLOv8 Nano
if [ ! -f "models/yolov8n.pt" ]; then
    echo "Downloading YOLOv8 Nano weights..."
    wget -q https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt -O models/yolov8n.pt
    echo "YOLOv8n downloaded."
fi

# 7. Enable Hardware Access in Docker Compose
echo "[7/8] Enabling USB Webcam and UART in docker-compose.yml..."
if grep -q "# devices:" docker-compose.yml; then
    sed -i 's/# devices:/devices:/' docker-compose.yml
    sed -i 's/#   - \/dev\/video0:\/dev\/video0/  - \/dev\/video0:\/dev\/video0/' docker-compose.yml
    sed -i 's/#   - \/dev\/ttyS0:\/dev\/ttyS0/  - \/dev\/ttyS0:\/dev\/ttyS0/' docker-compose.yml
    sed -i 's/# privileged: true/privileged: true/' docker-compose.yml
    echo "Hardware access enabled."
else
    echo "Hardware access already enabled."
fi

# 8. Build and Start Services
echo "[8/8] Building and starting Docker services..."
docker compose up -d --build

echo ""
echo "========================================="
echo "  ClassOS Deployment Complete!"
echo "========================================="
echo ""
echo "Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "API Docs:  http://$(hostname -I | awk '{print $1}')/docs"
echo ""
echo "Default Admin Login:"
echo "  Email:    admin@classos.local"
echo "  Password: changeme123"
echo ""
echo "IMPORTANT: Change the default admin password!"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop:      docker compose down"
echo ""
