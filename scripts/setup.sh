#!/bin/bash
# =============================================================
# ClassOS — Local Development Setup Script
# For development on any machine (Linux/macOS/WSL)
# =============================================================

set -e

echo "========================================="
echo "  ClassOS — Development Setup"
echo "========================================="

# 1. Create Python virtual environment
echo "[1/5] Creating Python virtual environment..."
python3.11 -m venv venv || python3 -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
echo "[2/5] Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Create .env if not exists
echo "[3/5] Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Set mock mode for fingerprint sensor in development
    sed -i 's/FINGERPRINT_MOCK_MODE=false/FINGERPRINT_MOCK_MODE=true/' .env
    echo "Created .env with fingerprint mock mode enabled for development."
fi

# 4. Create directories
echo "[4/5] Creating data directories..."
mkdir -p data/faces models logs

# 5. Download YOLOv8 Nano weights
echo "[5/5] Downloading YOLOv8 Nano model..."
if [ ! -f "models/yolov8n.pt" ]; then
    wget -q https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt -O models/yolov8n.pt
    echo "Model downloaded."
else
    echo "Model already exists."
fi

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Start PostgreSQL:"
echo "     docker compose up -d db"
echo ""
echo "  2. Seed the database:"
echo "     python -m scripts.seed_db"
echo ""
echo "  3. Start the backend:"
echo "     uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  4. Start the frontend (new terminal):"
echo "     cd frontend && npm install && npm run dev"
echo ""
