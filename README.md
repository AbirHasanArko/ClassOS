# 🎓 ClassOS — AI-Powered Classroom Attendance System

<p align="center">
  <strong>Smart attendance tracking using face recognition, head counting, and fingerprint verification</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-blue?logo=react" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Raspberry%20Pi-5-red?logo=raspberrypi" alt="Raspberry Pi">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?logo=docker" alt="Docker">
</p>

---

## 📋 Overview

ClassOS automates classroom attendance using AI-powered face recognition on a Raspberry Pi 5. Teachers start attendance sessions from a real-time web dashboard, the camera scans the classroom, and the system automatically identifies students using face recognition with a fingerprint fallback for low-confidence cases (hijab, masks, poor visibility).

### Key Features

- **Real-time face recognition** with confidence-based auto-marking
- **YOLOv8 Nano head counting** with mismatch detection
- **R307 fingerprint fallback** for occluded/low-confidence faces
- **Live video streaming** (MJPEG) to web dashboard
- **WebSocket real-time updates** for attendance events
- **Role-based access** (Admin, Teacher, Student)
- **Analytics & reporting** with charts and export
- **Dark/light mode** responsive dashboard
- **Docker deployment** with one command

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy               │
├──────────────────┬──────────────────────────────────┤
│   React Frontend │        FastAPI Backend            │
│   (Dashboard)    │   ┌─────────┬──────────────┐     │
│                  │   │ REST API│ WebSocket Mgr │     │
│   • Live Feed    │   ├─────────┴──────────────┤     │
│   • Attendance   │   │   Attendance Engine     │     │
│   • Analytics    │   ├────────┬───────────────┤     │
│   • Management   │   │AI Pipe │ Fingerprint   │     │
│                  │   │  line  │  Service      │     │
│                  │   ├────────┤               │     │
│                  │   │Camera  │  R307 UART    │     │
│                  │   │Service │               │     │
├──────────────────┴───┴────────┴───────────────┴─────┤
│                   PostgreSQL Database                 │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 Hardware Requirements

| Component | Model | Purpose |
|-----------|-------|---------|
| SBC | Raspberry Pi 5 (8GB) | Main compute |
| Camera | Pi Camera Module 3 | Face capture & video streaming |
| Fingerprint | R307 Optical Sensor | Fallback identity verification |

### Hardware Wiring (R307 → Pi 5)

| R307 Pin | Pi 5 GPIO | Color |
|----------|-----------|-------|
| VCC (3.3V) | Pin 1 (3.3V) | Red |
| GND | Pin 6 (GND) | Black |
| TX | Pin 10 (GPIO15/RXD1) | Yellow |
| RX | Pin 8 (GPIO14/TXD1) | Green |

> ⚠️ **Important**: Enable UART in `/boot/firmware/config.txt`:
> ```
> enable_uart=1
> dtoverlay=uart0
> ```

See [docs/hardware_wiring.md](docs/hardware_wiring.md) for detailed diagrams.

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Deploy with Docker

```bash
# Clone the repo
git clone https://github.com/yourusername/ClassOS.git
cd ClassOS

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Build and start all services
docker-compose up -d --build

# Access the dashboard
open http://localhost
```

### Default Login

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@classos.local | changeme123 |

> 🔒 **Change the default admin password immediately after first login.**

---

## 🛠️ Development Setup

### Backend

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Run migrations
python -m scripts.seed_db

# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

```bash
# Start PostgreSQL (Docker)
docker-compose up -d db

# Or use local PostgreSQL
createdb classos_db
psql classos_db < database/migrations/001_initial_schema.sql
```

---

## 📡 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [docs/api_reference.md](docs/api_reference.md) for full documentation.

---

## 📊 Recognition Logic

| Confidence | Action | Method |
|------------|--------|--------|
| > 90% | Auto-mark attendance | FACE |
| 70–90% | Request fingerprint verification | FINGERPRINT |
| < 70% | Label as unknown | — |

---

## 📁 Project Structure

```
ClassOS/
├── backend/              # FastAPI application
│   ├── auth/             # JWT authentication
│   ├── routers/          # API route handlers
│   ├── schemas/          # Pydantic validation models
│   └── websocket/        # Real-time WebSocket manager
├── frontend/             # React dashboard
│   └── src/
│       ├── api/          # Axios API client
│       ├── components/   # Reusable UI components
│       ├── contexts/     # React contexts (auth, theme, WS)
│       └── pages/        # Page components
├── ai_engine/            # Face recognition & head counting
├── camera_service/       # Camera abstraction & MJPEG streaming
├── fingerprint_service/  # R307 sensor driver
├── attendance_engine/    # Core attendance orchestration
├── database/             # DB connection & migrations
├── models/               # SQLAlchemy ORM models
├── docker/               # Dockerfiles
├── nginx/                # Reverse proxy config
├── scripts/              # Setup & deployment scripts
└── docs/                 # Guides & documentation
```

---

## 🧪 Testing

```bash
# Run backend tests
python -m pytest backend/tests/ -v

# Run frontend tests
cd frontend && npm test

# Hardware tests (on Pi 5)
python -m scripts.test_camera
python -m scripts.test_fingerprint
```

See [docs/testing_guide.md](docs/testing_guide.md) for comprehensive testing instructions.

---

## 🔒 Security

- JWT-based authentication with refresh tokens
- bcrypt password hashing (12 rounds)
- Role-based access control (Admin/Teacher/Student)
- CORS restrictions
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy ORM
- HTTPS-ready Nginx configuration
- Secure environment variable management

---

## 📝 License

This project is for educational purposes. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [face_recognition](https://github.com/ageitgey/face_recognition) by Adam Geitgey
- [YOLOv8](https://github.com/ultralytics/ultralytics) by Ultralytics
- [FastAPI](https://fastapi.tiangolo.com/) by Sebastián Ramírez
- [React](https://react.dev/) by Meta
