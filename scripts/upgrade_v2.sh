#!/bin/bash
# =============================================================
# ClassOS v2.0 Upgrade Script
# Run this on your Raspberry Pi 5 to upgrade from v1.x to v2.0
# =============================================================

set -e

echo "========================================="
echo "  ClassOS v2.0 Upgrade Script"
echo "========================================="

# 1. Update Database Schema
echo "[1/4] Upgrading Database Schema..."
cat << 'EOF' > /tmp/upgrade_db.py
import asyncio
from sqlalchemy import text
from database.connection import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE attendance_sessions ADD COLUMN mode VARCHAR(20) NOT NULL DEFAULT 'attendance';"))
            print("Successfully added 'mode' column to attendance_sessions.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate_column" in str(e).lower() or "42701" in str(e):
                print("Column 'mode' already exists. Skipping.")
            else:
                print(f"Error: {e}")
                raise

if __name__ == "__main__":
    asyncio.run(migrate())
EOF

if docker compose ps | grep -q "classos-backend"; then
    docker cp /tmp/upgrade_db.py classos-backend:/app/upgrade_db.py
    docker exec classos-backend python /app/upgrade_db.py
    docker exec classos-backend rm /app/upgrade_db.py
else
    export PYTHONPATH=$(pwd)
    python /tmp/upgrade_db.py
fi
rm /tmp/upgrade_db.py

# 2. Enable I2C
echo "[2/4] Enabling I2C for LCD Display..."
REBOOT_REQUIRED=false
if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    echo "I2C enabled. A reboot will be required."
    REBOOT_REQUIRED=true
else
    echo "I2C already enabled."
fi

# 3. Detect Cameras
echo "[3/4] Checking Cameras..."
cameras=$(ls /dev/video* 2>/dev/null | grep -E '/dev/video[0-9]+$')
cam_count=$(echo "$cameras" | wc -l)
if [ "$cam_count" -ge 2 ]; then
    cam1=$(echo "$cameras" | head -n 1)
    # RPi CSI cameras often create multiple nodes (e.g. video0, video1).
    # Second camera is usually video2 or video4.
    cam2=$(echo "$cameras" | sed -n '3p') 
    if [ -z "$cam2" ]; then
        cam2=$(echo "$cameras" | sed -n '2p')
    fi
    echo "Found Camera 0 at: $cam1"
    echo "Found Camera 1 at: $cam2"
    
    if [ -f .env ]; then
        cam2_index=$(echo $cam2 | sed 's/[^0-9]*//g')
        if grep -q "CAMERA_1_DEVICE_INDEX" .env; then
            sed -i "s/^CAMERA_1_DEVICE_INDEX=.*/CAMERA_1_DEVICE_INDEX=$cam2_index/" .env
        else
            echo "CAMERA_1_DEVICE_INDEX=$cam2_index" >> .env
        fi
        echo "Updated CAMERA_1_DEVICE_INDEX=$cam2_index in .env"
    fi
else
    echo "Warning: Less than 2 cameras found. Ensure both cameras are connected for v2.0 Head Count mode."
fi

# 4. Rebuild & Restart services
echo "[4/4] Rebuilding and Restarting ClassOS Services..."
docker compose down
docker compose up -d --build

echo "========================================="
echo "  Upgrade Complete!"
echo "========================================="
if [ "$REBOOT_REQUIRED" = true ]; then
    echo "WARNING: I2C was just enabled. You MUST reboot your Raspberry Pi now to use the LCD:"
    echo "  sudo reboot"
fi
