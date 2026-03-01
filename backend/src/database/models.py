from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


"""
Enums
"""
class AlcoholUse(str, Enum):
    NONE = "none"
    RARE = "rare"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    
class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    VIGOROUS = "vigorous"

class UserRole(str, Enum):
    PATIENT = "patient"
    PROFESSIONAL = "professional"

class SenderType(str, Enum):
    USER = "user"
    BOT = "bot"
    PROFESSIONAL = "professional"

class Classification(str, Enum):
    SAFE = "safe"
    NEEDS_REVIEW = "needs_review"
    EMERGENCY = "emergency"

class ChatStatus(str, Enum):
    OPEN = "open"
    WAITING = "waiting_for_professional"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


"""
Base models
"""
class BloodPressure(BaseModel):
    systolic: int = Field(..., ge=50, le=300, description="mmHg")
    diastolic: int = Field(..., ge=30, le=200, description="mmHg")

class PatientInfo(BaseModel):
    weight: float
    height: float
    age: int
    conditions: List[str] = []
    avg_blood_pressure: BloodPressure
    risk_factors: List[str] = []
    alcohol_use: AlcoholUse
    allergies: List[str] = []
    activity: ActivityLevel
    medications: List[str] = []
    heart_procedures: List[str] = []

class UserModel(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.PATIENT
    patient_info: Optional[PatientInfo] = None

class ChatModel(BaseModel):
    user_id: str
    status: ChatStatus
    assigned_professional_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class MessageModel(BaseModel):
    chat_id: str
    sender: SenderType
    content: str
    classification: Classification = Classification.SAFE
    flagged_for_human: bool = False
    created_at: datetime
    updated_at: datetime


"""
Request models
"""
class SendMessageRequest(BaseModel):
    message: str

class ProfessionalMessageRequest(BaseModel):
    message: str

class LoginRequest(BaseModel):
    email: str
    password: str


"""
Response models
"""

# Shared/generic
class StatusResponse(BaseModel):
    status: str
    message: str

class StatusWithUserResponse(BaseModel):
    status: str
    message: Optional[str] = None
    user: Optional[dict] = None

# Users
class CreateUserResponse(BaseModel):
    user_id: str
    message: str

class CheckSessionResponse(BaseModel):
    isLoggedIn: bool
    userId: Optional[str] = None

# Chat
class ChatReplyResponse(BaseModel):
    reply: str

# Professional
class MessageDetailResponse(BaseModel):
    id: str
    sender: SenderType
    content: str
    classification: Classification
    flagged_for_human: bool
    created_at: datetime
    updated_at: datetime

class ChatDetailResponse(BaseModel):
    id: str
    user_id: str
    status: str
    assigned_professional_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageDetailResponse]

class ChatQueueResponse(BaseModel):
    in_progress: List[ChatDetailResponse]
    waiting: List[ChatDetailResponse]
    closed: List[ChatDetailResponse]

class UserDetailResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    patient_info: Optional[PatientInfo] = None

class AuthResponse(BaseModel):
    token: str
    user: UserDetailResponse
