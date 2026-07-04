#!/bin/bash
# ClassOS — v4l2loopback bridge installer for Raspberry Pi 5 IMX519 (DUAL CAMERA)
# Creates virtual devices /dev/video42 and /dev/video43 that OpenCV can read.

set -e

VDEV_0=42  # Virtual device for Camera 0 (Attendance)
VDEV_1=43  # Virtual device for Camera 1 (Headcount)

echo "=========================================================="
echo "  ClassOS: Installing v4l2loopback for DUAL CSI Cameras   "
echo "=========================================================="

# 1. Install dependencies
echo "[1/4] Installing v4l2loopback and GStreamer..."
sudo apt-get update
sudo apt-get install -y linux-headers-rpi-v8 v4l2loopback-dkms v4l2loopback-utils \
    gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-libcamera

# 2. Configure module to load on boot for both devices
echo "[2/4] Configuring v4l2loopback module..."
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf > /dev/null
echo "options v4l2loopback devices=2 video_nr=${VDEV_0},${VDEV_1} card_label=\"ClassOS Cam 0\",\"ClassOS Cam 1\" exclusive_caps=1,1" | sudo tee /etc/modprobe.d/v4l2loopback.conf > /dev/null

# Unload if it's already loaded, then load with new options
sudo modprobe -r v4l2loopback 2>/dev/null || true
sudo modprobe v4l2loopback devices=2 video_nr=${VDEV_0},${VDEV_1} card_label="ClassOS Cam 0","ClassOS Cam 1" exclusive_caps=1,1

echo "  Created /dev/video${VDEV_0} and /dev/video${VDEV_1}"

# 3. Create the systemd services to continuously pipe the cameras
echo "[3/4] Creating systemd services..."

# Create parameterized wrapper script
sudo tee /usr/local/bin/classos-camera-bridge.sh > /dev/null <<'SCRIPT'
#!/bin/bash
# ClassOS Camera Bridge Parameterized Script
CAM_IDX=$1
VDEV_IDX=$2

if [ -z "$CAM_IDX" ] || [ -z "$VDEV_IDX" ]; then
    echo "Usage: $0 <camera_index> <video_device_number>"
    exit 1
fi

WIDTH=1280
HEIGHT=720
FPS=30

echo "Starting bridge: libcamera (cam ${CAM_IDX}) -> /dev/video${VDEV_IDX}"

exec rpicam-vid \
    --camera "$CAM_IDX" \
    -t 0 \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --framerate "$FPS" \
    --codec yuv420 \
    --autofocus-mode continuous \
    --nopreview \
    -o - \
  | gst-launch-1.0 -e \
    fdsrc \
    ! rawvideoparse width="$WIDTH" height="$HEIGHT" format=i420 framerate="${FPS}/1" \
    ! videoconvert \
    ! "video/x-raw,format=YUY2" \
    ! v4l2sink device="/dev/video${VDEV_IDX}"
SCRIPT

sudo chmod +x /usr/local/bin/classos-camera-bridge.sh

# Create systemd service for Camera 0
sudo tee /etc/systemd/system/classos-camera-bridge-0.service > /dev/null <<EOF
[Unit]
Description=ClassOS Camera Bridge 0 (Attendance)
After=network.target

[Service]
Type=simple
ExecStartPre=/usr/sbin/modprobe v4l2loopback devices=2 video_nr=${VDEV_0},${VDEV_1} card_label="ClassOS Cam 0","ClassOS Cam 1" exclusive_caps=1,1
ExecStart=/usr/local/bin/classos-camera-bridge.sh 0 ${VDEV_0}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Camera 1
sudo tee /etc/systemd/system/classos-camera-bridge-1.service > /dev/null <<EOF
[Unit]
Description=ClassOS Camera Bridge 1 (Headcount)
After=network.target

[Service]
Type=simple
ExecStartPre=/usr/sbin/modprobe v4l2loopback devices=2 video_nr=${VDEV_0},${VDEV_1} card_label="ClassOS Cam 0","ClassOS Cam 1" exclusive_caps=1,1
ExecStart=/usr/local/bin/classos-camera-bridge.sh 1 ${VDEV_1}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start the services
echo "[4/4] Enabling and starting bridge services..."
sudo systemctl daemon-reload

# If the old combined service exists, stop and disable it
sudo systemctl stop classos-camera-bridge.service 2>/dev/null || true
sudo systemctl disable classos-camera-bridge.service 2>/dev/null || true

sudo systemctl enable classos-camera-bridge-0.service
sudo systemctl restart classos-camera-bridge-0.service

sudo systemctl enable classos-camera-bridge-1.service
sudo systemctl restart classos-camera-bridge-1.service

# Wait a moment for startup
sleep 4

# Verify
echo ""
echo "=========================================================="
echo "  Service Status:"
sudo systemctl is-active classos-camera-bridge-0.service
sudo systemctl is-active classos-camera-bridge-1.service
echo ""
echo "  Check bridge 0 logs: sudo journalctl -u classos-camera-bridge-0 -f"
echo "  Check bridge 1 logs: sudo journalctl -u classos-camera-bridge-1 -f"
echo ""
echo "  Next steps:"
echo "    docker compose down"
echo "    docker compose up -d"
echo "=========================================================="
