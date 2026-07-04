#!/bin/bash
# ClassOS — v4l2loopback bridge installer for Raspberry Pi 5 IMX519
# Creates a virtual /dev/video10 that OpenCV (inside Docker) can read.
#
# Why /dev/video10?
#   The IMX519 CSI camera already occupies /dev/video0 (and video19-35) as raw
#   Bayer capture devices. We must use a free device number for v4l2loopback.
#
# How it works:
#   GStreamer's libcamerasrc captures processed frames from the IMX519 sensor
#   via libcamera and writes them to the v4l2loopback virtual device at
#   /dev/video10. Docker maps /dev/video10 into the container, and OpenCV
#   reads it like any standard USB webcam.

set -e

VDEV=42  # Virtual device number — /dev/video42 (must be above all real CSI nodes 0-35)

echo "=========================================================="
echo "  ClassOS: Installing v4l2loopback for IMX519 CSI Camera  "
echo "=========================================================="

# 1. Install dependencies
echo "[1/4] Installing v4l2loopback and GStreamer..."
sudo apt-get update
sudo apt-get install -y linux-headers-rpi-v8 v4l2loopback-dkms v4l2loopback-utils \
    gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-libcamera

# 2. Configure module to load on boot at /dev/video10
echo "[2/4] Configuring v4l2loopback module..."
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf > /dev/null
echo "options v4l2loopback video_nr=${VDEV} card_label=\"ClassOS Virtual Camera\" exclusive_caps=1" | sudo tee /etc/modprobe.d/v4l2loopback.conf > /dev/null

# Unload if it's already loaded, then load with new options
sudo modprobe -r v4l2loopback 2>/dev/null || true
sudo modprobe v4l2loopback video_nr=${VDEV} card_label="ClassOS Virtual Camera" exclusive_caps=1

echo "  Created /dev/video${VDEV}"

# Verify it's actually the loopback device (not a real camera)
DRIVER=$(v4l2-ctl -d /dev/video${VDEV} --all 2>&1 | grep "Driver name" | awk '{print $NF}')
if [ "$DRIVER" = "v4l2" ] || [ "$DRIVER" = "v4l2loopback" ]; then
    echo "  ✅ /dev/video${VDEV} is a v4l2loopback device"
else
    echo "  ⚠️  /dev/video${VDEV} driver is: ${DRIVER} (expected v4l2 loopback)"
    echo "  Trying to continue anyway..."
fi

# 3. Create the systemd service to continuously pipe the camera
echo "[3/4] Creating systemd service..."

# Create wrapper script: rpicam-vid (capture + ISP) → GStreamer v4l2sink (output)
# Why this hybrid approach?
#   - rpicam-vid properly handles IMX519 ISP processing (raw Bayer → YUV420)
#   - GStreamer's v4l2sink properly writes V4L2 frames to v4l2loopback
#   - libcamerasrc alone fails to negotiate processed output for IMX519
#   - ffmpeg's v4l2 output muxer fails with ioctl(VIDIOC_G_FMT)
sudo tee /usr/local/bin/classos-camera-bridge.sh > /dev/null <<SCRIPT
#!/bin/bash
# ClassOS Camera Bridge: IMX519 (rpicam-vid) → v4l2loopback (/dev/video${VDEV})

WIDTH=1280
HEIGHT=720
FPS=30

exec rpicam-vid \\
    --camera 0 \\
    -t 0 \\
    --width \$WIDTH \\
    --height \$HEIGHT \\
    --framerate \$FPS \\
    --codec yuv420 \\
    --nopreview \\
    -o - \\
  | gst-launch-1.0 -e \\
    fdsrc \\
    ! rawvideoparse width=\$WIDTH height=\$HEIGHT format=i420 framerate=\${FPS}/1 \\
    ! videoconvert \\
    ! "video/x-raw,format=YUY2" \\
    ! v4l2sink device=/dev/video${VDEV}
SCRIPT

sudo chmod +x /usr/local/bin/classos-camera-bridge.sh

# Create systemd service
sudo tee /etc/systemd/system/classos-camera-bridge.service > /dev/null <<EOF
[Unit]
Description=ClassOS libcamera to v4l2loopback Bridge (IMX519)
After=network.target

[Service]
Type=simple
ExecStartPre=/usr/sbin/modprobe v4l2loopback video_nr=${VDEV} card_label="ClassOS Virtual Camera" exclusive_caps=1
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
sleep 4

# Verify
echo ""
echo "=========================================================="
STATUS=$(sudo systemctl is-active classos-camera-bridge.service)
if [ "$STATUS" = "active" ]; then
    echo "  ✅ Bridge service is RUNNING!"
    echo "  ✅ /dev/video${VDEV} is ready for Docker"
else
    echo "  ❌ Bridge service failed. Debug with:"
    echo "     sudo journalctl -u classos-camera-bridge --no-pager -n 20"
fi
echo ""
echo "  Next steps:"
echo "    1. Set CAMERA_DEVICE_INDEX=${VDEV} in your .env file"
echo "    2. docker compose down"
echo "    3. docker compose up -d"
echo "=========================================================="
