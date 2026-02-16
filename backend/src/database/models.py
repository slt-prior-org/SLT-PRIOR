from pydantic import BaseModel, Field
from typing import List, Optional

class UserModel(BaseModel):
    weight: float
    height: float
    conditions: List[str] = []
    avg_blood_pressure: str
    risk_factors: List[str] = []
    alcohol_use: str
    allergies: List[str] = []
    activity: str
    medications: List[str] = []
    heart_procedures: List[str] = []

class RegisterModel(BaseModel):
    email: str
    password: str
    role: str
    patient_info: Optional[UserModel] = None