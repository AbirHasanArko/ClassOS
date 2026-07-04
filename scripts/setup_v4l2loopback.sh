#!/bin/bash
# ClassOS — v4l2loopback bridge installer for Raspberry Pi 5 IMX519
# Creates a virtual /dev/video0 that OpenCV (inside Docker) can read.
#
# How it works:
#   rpicam-vid captures raw YUV420 from the IMX519 sensor via libcamera,
#   pipes it to ffmpeg which re-wraps the frames into proper V4L2 format,
#   and writes them to the v4l2loopback virtual device at /dev/video0.

set -e

echo "=========================================================="
echo "  ClassOS: Installing v4l2loopback for IMX519 CSI Camera  "
echo "=========================================================="

# 1. Install dependencies
echo "[1/4] Installing v4l2loopback-dkms and ffmpeg..."
sudo apt-get update
sudo apt-get install -y linux-headers-rpi-v8 v4l2loopback-dkms v4l2loopback-utils ffmpeg

# 2. Configure module to load on boot and create /dev/video0
echo "[2/4] Configuring v4l2loopback module..."
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf > /dev/null
echo "options v4l2loopback video_nr=0 card_label=\"ClassOS Virtual Camera\" exclusive_caps=1" | sudo tee /etc/modprobe.d/v4l2loopback.conf > /dev/null

# Unload if it's already loaded, then load with new options
sudo modprobe -r v4l2loopback 2>/dev/null || true
sudo modprobe v4l2loopback video_nr=0 card_label="ClassOS Virtual Camera" exclusive_caps=1

# 3. Create the systemd service to continuously pipe the camera
echo "[3/4] Creating systemd service..."

# Create wrapper script that pipes rpicam-vid → ffmpeg → /dev/video0
sudo tee /usr/local/bin/classos-camera-bridge.sh > /dev/null <<'SCRIPT'
#!/bin/bash
# ClassOS Camera Bridge: IMX519 (libcamera) → v4l2loopback (/dev/video0)
#
# rpicam-vid outputs raw YUV420 to stdout.
# ffmpeg reads it as rawvideo and writes proper V4L2 frames to /dev/video0.

WIDTH=1280
HEIGHT=720
FPS=30

exec rpicam-vid \
    --camera 0 \
    -t 0 \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --framerate "$FPS" \
    --codec yuv420 \
    --nopreview \
    -o - \
  | ffmpeg \
    -f rawvideo \
    -pixel_format yuv420p \
    -video_size "${WIDTH}x${HEIGHT}" \
    -framerate "$FPS" \
    -i pipe:0 \
    -f v4l2 \
    -pix_fmt yuyv422 \
    /dev/video0
SCRIPT

sudo chmod +x /usr/local/bin/classos-camera-bridge.sh

# Create systemd service
sudo tee /etc/systemd/system/classos-camera-bridge.service > /dev/null <<EOF
[Unit]
Description=ClassOS libcamera to v4l2loopback Bridge (IMX519)
After=network.target

[Service]
Type=simple
ExecStartPre=/usr/sbin/modprobe v4l2loopback video_nr=0 card_label="ClassOS Virtual Camera" exclusive_caps=1
ExecStart=/usr/local/bin/classos-camera-bridge.sh
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

# Wait a moment for startup
sleep 3

# Verify
echo ""
echo "=========================================================="
if [ -e /dev/video0 ]; then
    echo "  ✅ /dev/video0 exists!"
else
    echo "  ❌ /dev/video0 not found — check: sudo systemctl status classos-camera-bridge"
fi
echo ""
echo "  Check bridge status:  sudo systemctl status classos-camera-bridge"
echo "  View live logs:       sudo journalctl -u classos-camera-bridge -f"
echo ""
echo "  Next steps:"
echo "    docker compose down"
echo "    docker compose up -d"
echo "=========================================================="
