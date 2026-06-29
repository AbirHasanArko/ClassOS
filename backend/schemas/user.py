from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from models.user import UserRole

class UserBase(BaseModel):
    email: str
    role: UserRole

class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str
    student_id: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None

class UserOut(UserBase):
    id: UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None

class UserListOut(UserOut):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    profile_id: Optional[UUID] = None
