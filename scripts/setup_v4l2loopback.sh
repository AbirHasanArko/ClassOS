#!/bin/bash
# ClassOS — v4l2loopback bridge installer for Raspberry Pi 5 IMX519

set -e

echo "=========================================================="
echo "  ClassOS: Installing v4l2loopback for IMX519 CSI Camera  "
echo "=========================================================="

# 1. Install dependencies
echo "[1/4] Installing v4l2loopback-dkms..."
sudo apt-get update
sudo apt-get install -y linux-headers-rpi-v8 v4l2loopback-dkms v4l2loopback-utils

# 2. Configure module to load on boot and create /dev/video0
echo "[2/4] Configuring v4l2loopback module..."
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf > /dev/null
echo "options v4l2loopback video_nr=0 card_label=\"ClassOS Virtual Camera\" exclusive_caps=1" | sudo tee /etc/modprobe.d/v4l2loopback.conf > /dev/null

# Unload if it's already loaded, then load with new options
sudo modprobe -r v4l2loopback || true
sudo modprobe v4l2loopback video_nr=0 card_label="ClassOS Virtual Camera" exclusive_caps=1

# 3. Create the systemd service to continuously pipe the camera
echo "[3/4] Creating systemd service..."

sudo tee /etc/systemd/system/classos-camera-bridge.service > /dev/null <<EOF
[Unit]
Description=ClassOS libcamera to v4l2loopback Bridge
After=network.target

[Service]
Type=simple
User=pi
ExecStartPre=/usr/sbin/modprobe v4l2loopback video_nr=0 card_label="ClassOS Virtual Camera" exclusive_caps=1
# Grabs frames from Camera 0 (IMX519) in YUV420 format and streams directly into the virtual /dev/video0
ExecStart=/usr/bin/libcamera-vid --camera 0 -t 0 --width 1280 --height 720 --framerate 30 --codec yuv420 -o /dev/video0 --inline
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start the service
echo "[4/4] Enabling and starting bridge service..."
sudo systemctl daemon-reload
sudo systemctl enable classos-camera-bridge.service
sudo systemctl restart classos-camera-bridge.service

echo "=========================================================="
echo "  Installation Complete!"
echo "  Verify /dev/video0 exists: ls -la /dev/video0"
echo "  Check bridge status: sudo systemctl status classos-camera-bridge"
echo "=========================================================="
