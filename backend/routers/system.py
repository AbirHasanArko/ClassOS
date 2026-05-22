from fastapi import APIRouter
import platform
import psutil

router = APIRouter()

@router.get("/status")
async def get_system_status():
    """Returns basic system resources status"""
    return {
        "os": platform.system(),
        "release": platform.release(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
