from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class EnrollRequest(BaseModel):
    student_id: UUID
    
class VerifyResponse(BaseModel):
    success: bool
    student_id: Optional[UUID] = None
    message: str

class StatusResponse(BaseModel):
    is_connected: bool
    is_mock_mode: bool
