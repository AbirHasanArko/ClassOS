<div align="center">
  <h1>ClassOS: AI-Powered Embedded Classroom Attendance System</h1>
  <p>
    <strong>The ultimate, fully automated classroom attendance solution. 
    <br>Powered by Computer Vision, Hardware Biometrics, and a Modern Web Stack on the Edge.</strong>
  </p>

  <p>
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-blue?logo=react" alt="React">
  <img src="https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Raspberry%20Pi-5-red?logo=raspberrypi" alt="Raspberry Pi">
  <img src="https://img.shields.io/badge/Docker-Ready-blue?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/YOLOv8-Nano-yellow" alt="YOLOv8">
</p>
</div>  
  
---

## 👨‍💻 Developers

**Abir Hasan Arko**  
🐙 [GitHub](https://github.com/AbirHasanArko) | 💼 [LinkedIn](https://www.linkedin.com/in/abirhasanarko/)

**Md Shomik Shahriar**  
🐙 [GitHub](https://github.com/Hapi-Guy) | 💼 [LinkedIn](https://www.linkedin.com/in/shomik101001/)

---

## 📑 Table of Contents

- [Core Features](#-core-features)
- [Technology Stack](#️-technology-stack)
- [Why ClassOS is One of a Kind](#-why-classos-is-one-of-a-kind)
- [Deep Dive: The AI Models](#-deep-dive-the-ai-models)
- [System Architecture](#-system-architecture)
- [AI & Logic Pipeline](#-ai--logic-pipeline)
- [Embedded Hardware Design](#-embedded-hardware-design)
- [Web Dashboard & Analytics](#-web-dashboard--analytics)
- [Step-by-Step Usage Guide](#-step-by-step-usage-guide)
- [Quick Start Deployment](#-quick-start-deployment)
- [Development Setup](#️-development-setup)
- [Security & Privacy](#-security--privacy)
- [Future Roadmap](#️-future-roadmap)
- [Extended Documentation](#-extended-documentation)
- [License & Acknowledgments](#-license--acknowledgments)

---

## 🚀 Core Features

- **Automated AI Face Recognition:** Real-time face detection using dlib algorithms with dynamic confidence-based auto-marking.
- **YOLOv8 Head Counting:** Nano-model AI sweeps the classroom to detect mismatched attendance (e.g. 20 students recognized, but 25 heads counted).
- **R307 Biometric Fallback:** Seamless fallback to physical fingerprint scanning over UART for occluded faces (hijabs, masks, poor lighting).
- **Live MJPEG Video Streaming:** Teachers watch the AI pipeline process the classroom feed in real-time from their web dashboard.
- **Real-Time WebSocket Sync:** As students are detected, their names instantly appear on the teacher's screen without refreshing.
- **Full-Stack Analytics:** Automatic data aggregation with CSV exports, visual charts, and historical session logs.
- **Role-Based Access Control:** Distinct experiences for Admins, Teachers, and Students.
- **Ghost-Session Resiliency:** The backend automatically recovers and cleans up abandoned sessions if a teacher's laptop disconnects unexpectedly.
- **One-Command Deployment:** Completely containerized with Docker Compose.

---

## 🛠️ Technology Stack

**Frontend**
- **Framework:** React 18 with Vite
- **Styling:** Tailwind CSS + UI components inspired by shadcn/ui
- **State Management:** React Context API
- **Charts:** Chart.js (via react-chartjs-2)

**Backend**
- **Framework:** FastAPI (Python 3.11)
- **Database ORM:** SQLAlchemy (Async)
- **Authentication:** JWT (JSON Web Tokens) with bcrypt
- **Real-time:** WebSockets for live attendance broadcasting

**AI & Computer Vision**
- **Face Recognition:** dlib (ResNet-based 128D embeddings)
- **Object Detection:** YOLOv8 Nano by Ultralytics
- **Image Processing:** OpenCV (cv2)

**Infrastructure & Hardware**
- **Database:** PostgreSQL 16
- **Deployment:** Docker & Docker Compose
- **Hardware:** Raspberry Pi 5
- **Biometrics:** R307 Optical Fingerprint Sensor (via UART)

---

## 🌟 Why ClassOS is One of a Kind

Most automated attendance systems fall into two categories: cloud-dependent APIs that are slow and compromise student privacy, or fragile local scripts that lack a modern user interface. 

**ClassOS bridges the gap by delivering a state-of-the-art enterprise architecture running entirely on the Edge.** 
By leveraging the Raspberry Pi 5, ClassOS handles computationally heavy AI inferencing locally, orchestrates low-level hardware serial communication (UART) for fingerprint fallback, and serves a beautiful, high-performance React dashboard to any device on the network—all without requiring an active internet connection. It is a complete, self-contained operating environment for the modern classroom.

---

## 🧠 Deep Dive: The AI Models

ClassOS uses a dual-model approach to ensure extremely high accuracy without bogging down the Raspberry Pi's CPU.

1. **Face Embedding (dlib / ResNet):** When a student is enrolled, ClassOS extracts a 128-dimensional embedding of their face using a ResNet network trained on 3 million faces. During a live session, the system calculates the Euclidean distance between the live camera face and the stored database embeddings to generate a confidence percentage.
2. **Crowd Verification (YOLOv8 Nano):** Face recognition alone can miss students sitting far back or looking down. To prevent proxy attendance and ensure total accuracy, we run Ultralytics' YOLOv8-nano model in the background to count the total number of human heads in the frame. If the head count exceeds the recognized face count, the teacher is alerted.

---

## 🏗️ System Architecture

ClassOS utilizes a heavily decoupled microservice-like structure packaged securely inside Docker containers.

```mermaid
graph TD
    subgraph Frontend [React Frontend]
        UI[User Dashboard]
        WS_Client[WebSocket Client]
        Stream_Viewer[MJPEG Viewer]
    end

    subgraph Backend [FastAPI Backend]
        API[REST APIs]
        WS_Mgr[WebSocket Manager]
        Stream_Serv[Camera Streaming Engine]
    end

    subgraph AI_Engine [Background AI Engine]
        Face[Face Recognition]
        Yolo[YOLOv8 Head Counter]
        Orchestrator[Attendance Orchestrator]
    end

    subgraph Hardware [Edge Hardware Integration]
        Cam[(Webcam)]
        R307[(R307 Fingerprint)]
    end

    DB[(PostgreSQL)]

    %% Connections
    UI -- Axios HTTP --> API
    WS_Client -- Real-time Events --> WS_Mgr
    Stream_Viewer -- HTTP Chunked --> Stream_Serv

    API <--> DB
    Orchestrator <--> DB

    Cam --> Stream_Serv
    Stream_Serv -- Async Frames --> Face
    Stream_Serv -- Async Frames --> Yolo
    
    Face --> Orchestrator
    Yolo --> Orchestrator
    R307 -- UART Serial --> Orchestrator

    Orchestrator -- Broadcasts --> WS_Mgr
```

---

## 🤖 AI & Logic Pipeline

To prevent duplicate database writes and handle uncertain identifications, ClassOS implements a strict state-machine flow for every detected face.

```mermaid
flowchart TD
    A[New Video Frame] --> B[Detect Faces]
    B --> C{Generate Embedding}
    C -- Match Found --> D[Calculate Confidence Score]
    C -- No Match --> E[Draw Red 'Unknown' Box]
    
    D --> F{Confidence >= 75%?}
    F -- Yes --> G[Auto-Mark Present]
    G --> H[(Save to Database)]
    H --> I[Broadcast 'Present' via WebSocket]
    I --> J[Draw Green Box]
    
    F -- No, but >= 60% --> K[Trigger Verification Flow]
    K --> L[Draw Orange 'Verify FP' Box]
    L --> M[Prompt Teacher UI]
    M --> N[Wait for R307 Fingerprint Scan]
    N -- Valid Scan --> H
```

### Recognition Thresholds

| Confidence Score | Action Taken | Logging Method |
|------------------|--------------|----------------|
| **> 75%** | Automatic Attendance | `FACE` |
| **60% - 75%** | Fingerprint Verification Required | `FINGERPRINT` |
| **< 60%** | Ignored / Labeled Unknown | None |

---

## 🔌 Embedded Hardware Design

ClassOS requires direct hardware integration. The Raspberry Pi 5 orchestrates standard USB protocols alongside direct GPIO Serial Communication.

| Component | Model | Interface | Purpose |
|-----------|-------|-----------|---------|
| Compute | Raspberry Pi 5 (8GB) | — | Main edge server |
| Camera | UVC-compatible Webcam | USB 3.0 | Realtime video capture |
| Biometric | R307 Optical Sensor | UART (GPIO) | Identity fallback verification |

### R307 UART Wiring Guide

| R307 Pin | Pi 5 GPIO Pin | Wire Color |
|----------|---------------|------------|
| VCC (3.3V) | Pin 1 (3.3V) | Red |
| GND | Pin 6 (GND) | Black |
| TX | Pin 10 (GPIO15 / RXD1) | Yellow |
| RX | Pin 8 (GPIO14 / TXD1) | Green |

> ⚠️ **Important:** You must enable UART on the Raspberry Pi for the fingerprint scanner to work. Add `enable_uart=1` and `dtoverlay=uart0` to your `/boot/firmware/config.txt`.

---

## 💻 Web Dashboard & Analytics

The frontend is a beautifully designed SPA (Single Page Application) built with **React, Vite, and Tailwind CSS**. 

**Dashboard Capabilities:**
- **Live Attendance View:** Watch the AI draw bounding boxes over the classroom in real time while a live-updating roster syncs beside it.
- **Analytics & History:** View historical session logs, overall attendance rates, and visualize pie charts differentiating face vs fingerprint authentications.
- **CSV Data Export:** Generate downloadable `.csv` spreadsheets of session data with a single click.
- **Face/Fingerprint Enrollment:** Admins can securely enroll new students directly from the browser using the Pi's connected hardware.

---

## 📖 Step-by-Step Usage Guide

1. **Student Account Creation:** 
   - An Admin navigates to the **Students** tab and clicks "Add Student".
   - The admin inputs the student's ID, Name, and Email. This creates a student profile and a login account (default password: `student123`).
2. **Student Self-Service (Optional but recommended):**
   - Students can log in to their own portal.
   - From the **Face Enrollment** tab, students can use their webcam or upload photos to register their facial data.
   - From the **Available Courses** tab, students can enroll themselves into the classes they are taking.
   - From the **My Attendance** tab, students can monitor their attendance records and percentages.
3. **Admin/Teacher Course Configuration:**
   - The teacher creates a new Course (e.g., "CS101").
   - If students haven't self-enrolled, the teacher can manually select which students are enrolled in that class.
   - Admins can also manually enroll biometrics using the physical hardware.
4. **Running a Session:**
   - At the start of a lecture, the teacher logs into ClassOS, goes to the **Attendance** tab, and clicks "Start Session".
   - The Raspberry Pi immediately boots up the AI background thread, turns on the camera, and begins streaming the live MJPEG feed to the dashboard.
   - As students walk into the room, bounding boxes appear around their faces. Green boxes indicate they have been successfully logged in the database.
5. **Exporting Data:**
   - After class, the teacher clicks "End Session". They can then navigate to the **Analytics** tab to download a CSV of the exact time and method (Face vs Fingerprint) each student used to check in.

---

## ⚡ Quick Start Deployment

Deploying the entire infrastructure is done with a single Docker command.

### Prerequisites
- Docker Engine & Docker Compose
- Raspberry Pi 5 running 64-bit Debian/Ubuntu

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/AbirHasanArko/ClassOS.git
cd ClassOS

# 2. Configure environment variables
cp .env.example .env

# 3. Build and launch all containers
docker compose up -d --build

# 4. Access the web dashboard
open http://<YOUR_PI_IP_ADDRESS>:5173
```

### Default Admin Credentials
- **Email:** `admin@classos.local`
- **Password:** `changeme123` *(Change this immediately!)*

---

## 🛠️ Development Setup

If you wish to run the app outside of Docker for development:

### Backend
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python -m scripts.seed_db
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🔒 Security & Privacy

- **JWT Authentication:** Secure API endpoints with expiring tokens.
- **Edge Processing:** Images are processed locally in RAM and discarded immediately. Video feeds and facial data are **never** sent to external cloud servers, protecting student privacy.
- **Password Hashing:** Strict bcrypt hashing (12 rounds) for all user passwords.
- **Database Safety:** SQLAlchemy ORM strictly prevents SQL Injection attacks.

---

## 🗺️ Future Roadmap

- [ ] **Multi-Camera Support:** Support for an array of RTSP IP cameras stationed around a large lecture hall.
- [ ] **Mobile App:** A native iOS/Android application for teachers to start sessions from their phone.
- [ ] **Automated Email Reports:** Send weekly attendance reports directly to students.
- [ ] **RFID Integration:** Add a tertiary fallback mechanism using standard student RFID cards.

---

## 📚 Extended Documentation

For deeper technical dives, please refer to the dedicated documentation files:

- 📊 **[Database ER Diagram (ER_DIAGRAM.md)](docs/ER_DIAGRAM.md)**
- 📖 **[Workflow Guide (workflow_guide.md)](docs/workflow_guide.md)**
- 🔌 **[Hardware Wiring Guide (hardware_wiring.md)](docs/hardware_wiring.md)**
- 🚀 **[Deployment Guide (deployment_guide.md)](docs/deployment_guide.md)**
- 🧪 **[Testing Guide (testing_guide.md)](docs/testing_guide.md)**
- 📡 **[API Reference (api_reference.md)](docs/api_reference.md)**  


---

## 📝 License & Acknowledgments

This project is open-source and intended for educational innovation in smart classrooms. 

**Powered By:**
- [FastAPI](https://fastapi.tiangolo.com/) by Sebastián Ramírez
- [React](https://react.dev/) by Meta
- [face_recognition](https://github.com/ageitgey/face_recognition) by Adam Geitgey
- [YOLOv8](https://github.com/ultralytics/ultralytics) by Ultralytics
