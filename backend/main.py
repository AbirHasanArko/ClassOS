"""
ClassOS — FastAPI Application Factory
Main entry point for the backend. Mounts routers, configures middleware,
and manages application lifecycle events.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Runs on startup: initialize DB, load AI models, create directories.
    Runs on shutdown: cleanup resources.
    """
    # ----- Startup -----
    print(f"🚀 Starting {settings.APP_NAME} ({settings.APP_ENV})")

    # Create required directories
    os.makedirs(settings.FACE_IMAGES_DIR, exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Initialize database tables
    from database.connection import engine
    from database.base import Base
    # Import all models so they register with Base.metadata
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables initialized")

    # Load AI models (lazy — done in ai_engine on first use)
    print("✅ Application ready")

    # Start the Attendance Engine (background loop: camera → AI → DB)
    from attendance_engine.engine import engine as attendance_engine
    await attendance_engine.start()
    print("✅ Attendance engine started")

    yield

    # ----- Shutdown -----
    print("🛑 Shutting down ClassOS...")

    # Stop attendance engine and camera
    from attendance_engine.engine import engine as attendance_engine
    attendance_engine.is_running = False
    from camera_service.camera import camera
    camera.stop()
    print("✅ Camera and attendance engine stopped")

    from database.connection import engine
    await engine.dispose()
    print("✅ Database connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Classroom Attendance System",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ----- CORS Middleware -----
    # Configure CORS
    origins = settings.cors_origin_list

    if "*" in origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=".*", # Workaround for allow_credentials=True with wildcard
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ----- Register Routers -----
    from backend.auth.router import router as auth_router
    from backend.routers.students import router as students_router
    from backend.routers.courses import router as courses_router
    from backend.routers.attendance import router as attendance_router
    from backend.routers.users import router as users_router
    from backend.routers.analytics import router as analytics_router
    from backend.routers.system import router as system_router
    from backend.routers.face import router as face_router
    from backend.websocket.router import router as ws_router
    from camera_service.stream import router as stream_router
    from fingerprint_service.router import router as fingerprint_router

    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(students_router, prefix="/api/students", tags=["Students"])
    app.include_router(courses_router, prefix="/api/courses", tags=["Courses"])
    app.include_router(attendance_router, prefix="/api/attendance", tags=["Attendance"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(system_router, prefix="/api/system", tags=["System"])
    app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
    app.include_router(stream_router, prefix="/api/stream", tags=["Video Stream"])
    app.include_router(fingerprint_router, prefix="/api/fingerprint", tags=["Fingerprint"])
    app.include_router(face_router, prefix="/api/students", tags=["Face Registration"])

    # ----- Health Check -----
    @app.get("/api/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
        }

    return app


# Create the app instance
app = create_app()
