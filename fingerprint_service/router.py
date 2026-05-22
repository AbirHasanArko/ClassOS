from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from fingerprint_service.sensor import fp_sensor
from fingerprint_service.schemas import VerifyResponse, StatusResponse, EnrollRequest
from backend.dependencies import get_db, require_role
from models.user import User, UserRole
from models.student import Student
from models.fingerprint import FingerprintData

router = APIRouter()

@router.get("/status", response_model=StatusResponse)
async def get_sensor_status():
    """Check if the fingerprint sensor is connected and responsive."""
    return {
        "is_connected": fp_sensor.get_status(),
        "is_mock_mode": fp_sensor.mock_mode
    }

@router.post("/enroll", status_code=status.HTTP_200_OK)
async def enroll_fingerprint(
    request: EnrollRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.TEACHER]))
):
    """Start the fingerprint enrollment process for a student."""
    # Check if student exists
    result = await db.execute(select(Student).where(Student.id == request.student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Determine next available sensor ID (1-200)
    # This is a simplification; in a real app you might track available IDs
    max_id_result = await db.execute(select(func.max(FingerprintData.sensor_id)))
    next_sensor_id = (max_id_result.scalar() or 0) + 1
    
    if next_sensor_id > 200:
        raise HTTPException(status_code=400, detail="Fingerprint sensor memory full")

    # In a real implementation, this would be an async long-polling endpoint or WebSocket
    # because the enroll flow requires the user to place and lift their finger.
    # For this architecture, we trigger the synchronous flow.
    success = fp_sensor.enroll_flow(next_sensor_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enroll fingerprint on sensor")
        
    # Save to database
    fp_data = FingerprintData(
        student_id=request.student_id,
        sensor_id=next_sensor_id,
        is_enrolled=True
    )
    db.add(fp_data)
    
    # Update student record
    student.fingerprint_registered = True
    
    await db.commit()
    return {"message": "Fingerprint enrolled successfully"}

@router.post("/verify", response_model=VerifyResponse)
async def verify_fingerprint(
    db: AsyncSession = Depends(get_db)
    # Removed require_role so the standalone pi terminal can call it if needed,
    # or it can be called via the frontend with token.
):
    """
    Trigger a fingerprint scan and match against DB.
    Used during attendance when face recognition confidence is low.
    """
    success, match_id = fp_sensor.verify_flow()
    
    if not success or match_id is None:
        return {"success": False, "message": "No match found or sensor error"}
        
    # Find student by sensor ID
    stmt = select(FingerprintData).where(FingerprintData.sensor_id == match_id)
    result = await db.execute(stmt)
    fp_data = result.scalar_one_or_none()
    
    if not fp_data:
        return {"success": False, "message": "Match found on sensor but not in database"}
        
    return {
        "success": True,
        "student_id": fp_data.student_id,
        "message": "Verified successfully"
    }
