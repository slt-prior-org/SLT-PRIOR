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
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    conditions: List[str] = []
    avg_blood_pressure: Optional[BloodPressure] = None
    risk_factors: List[str] = []
    alcohol_use: Optional[AlcoholUse] = None
    allergies: List[str] = []
    activity: Optional[ActivityLevel] = None
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

class SourceItem(BaseModel):
    index: int
    source: str
    pages: List[int] = []
    preview: Optional[str] = None

class MessageModel(BaseModel):
    chat_id: str
    sender: SenderType
    content: str
    classification: Classification = Classification.SAFE
    flagged_for_human: bool = False
    sources: List[SourceItem] = []
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
    classification: str
    sources: List[SourceItem] = []
    requires_professional: Optional[bool] = None
    requires_confirmation: Optional[bool] = None
    classification_reasoning: Optional[str] = None
    guideline_excerpt: Optional[str] = None
    guideline_source: Optional[str] = None

class ChatSummaryItem(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

# Professional
class MessageDetailResponse(BaseModel):
    id: str
    sender: SenderType
    content: str
    classification: Classification
    flagged_for_human: bool
    sources: List[SourceItem] = []
    created_at: datetime
    updated_at: datetime

class SendChatMessageResponse(BaseModel):
    userMessage: MessageDetailResponse
    botMessage: Optional[MessageDetailResponse] = None
    requires_professional: bool = False
    requires_confirmation: bool = False
    guideline_excerpt: Optional[str] = None
    guideline_source: Optional[str] = None
    classification_reasoning: Optional[str] = None

class ChatDetailResponse(BaseModel):
    id: str
    user_id: str
    status: ChatStatus
    assigned_professional_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageDetailResponse]
    # Summarizer fields — only populated in GET /chats/{id}, None in queue view
    patient_context: Optional[PatientInfo] = None
    chat_summary: Optional[str] = None
    draft_response: Optional[str] = None
    requires_approval: Optional[bool] = None

class SmallChatResponse(BaseModel):
    id: str
    user_id: str
    status: ChatStatus
    assigned_professional_id: Optional[str] = None
    last_message: str
    created_at: datetime
    updated_at: datetime

class ChatQueueResponse(BaseModel):
    in_progress: List[SmallChatResponse]
    waiting: List[SmallChatResponse]
    closed: List[SmallChatResponse]

class UserDetailResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    patient_info: Optional[PatientInfo] = None

class AuthResponse(BaseModel):
    token: str
    user: UserDetailResponse
