import pytest
import sys
import os
from datetime import datetime
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.models import (
    BloodPressure, UserModel, ChatModel, MessageModel,
    UserRole, ChatStatus, SenderType, Classification, AlcoholUse, ActivityLevel
)

pytestmark = pytest.mark.unit


class TestBloodPressure:
    def test_valid_values(self):
        bp = BloodPressure(systolic=120, diastolic=80)
        assert bp.systolic == 120 # systolic border values 50-300
        assert bp.diastolic == 80 # diastolic border values 30-200

    def test_systolic_too_low(self):
        with pytest.raises(ValidationError):
            BloodPressure(systolic=10, diastolic=80)  # below ge=50

    def test_systolic_too_high(self):
        with pytest.raises(ValidationError):
            BloodPressure(systolic=999, diastolic=80)  # above le=300

    def test_diastolic_too_low(self):
        with pytest.raises(ValidationError):
            BloodPressure(systolic=120, diastolic=5)  # below ge=30

    def test_diastolic_too_high(self):
        with pytest.raises(ValidationError):
            BloodPressure(systolic=120, diastolic=999)  # above le=200


class TestUserModel:
    '''
    test valid creation,
    missing required fields (email, password),
    default role is PATIENT,
    invalid role string
    '''
    def test_valid_values(self):
        um = UserModel(email="test@test.com", password="testword123")
        assert um.email == "test@test.com"
        assert um.password == "testword123"
        assert um.role == UserRole.PATIENT

    def test_email_missing(self):
        with pytest.raises(ValidationError):
            UserModel(password="testword123")
    
    def test_password_missing(self):
        with pytest.raises(ValidationError):
            UserModel(email="test@test.com")
    
    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            UserModel(email="test@gmail.com", password="testword123", role= "wrongrole")
    

class TestChatModel:
    '''
    test valid creation, missing required fields, invalid ChatStatus string
    '''
    now = datetime.now()

    def test_valid_values(self):
        cm = ChatModel(user_id="user_id_1", status=ChatStatus.OPEN, created_at=self.now, updated_at=self.now)
        assert cm.user_id == "user_id_1"
        assert cm.status == ChatStatus.OPEN
        assert cm.created_at == self.now
        assert cm.updated_at == self.now

    def test_user_id_missing(self):
        with pytest.raises(ValidationError):
            ChatModel(status=ChatStatus.OPEN, created_at=self.now, updated_at=self.now)

    def test_status_missing(self):
        with pytest.raises(ValidationError):
            ChatModel(user_id="user_id_1", created_at=self.now, updated_at=self.now)

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            ChatModel(user_id="user_id_1", status="wrongstatus", created_at=self.now, updated_at=self.now)

class TestMessageModel:
    '''
    test valid creation, missing required fields, default classification is SAFE, default flagged_for_human is False
    '''
    now = datetime.now()

    def test_valid_values(self):
        mm = MessageModel(chat_id="chat_1", sender=SenderType.USER, content="hello", created_at=self.now, updated_at=self.now)
        assert mm.chat_id == "chat_1"
        assert mm.sender == SenderType.USER
        assert mm.content == "hello"

    def test_default_classification_is_safe(self):
        mm = MessageModel(chat_id="chat_1", sender=SenderType.USER, content="hello", created_at=self.now, updated_at=self.now)
        assert mm.classification == Classification.SAFE

    def test_default_flagged_for_human_is_false(self):
        mm = MessageModel(chat_id="chat_1", sender=SenderType.USER, content="hello", created_at=self.now, updated_at=self.now)
        assert mm.flagged_for_human == False

    def test_chat_id_missing(self):
        with pytest.raises(ValidationError):
            MessageModel(sender=SenderType.USER, content="hello", created_at=self.now, updated_at=self.now)

    def test_sender_missing(self):
        with pytest.raises(ValidationError):
            MessageModel(chat_id="chat_1", content="hello", created_at=self.now, updated_at=self.now)

    def test_content_missing(self):
        with pytest.raises(ValidationError):
            MessageModel(chat_id="chat_1", sender=SenderType.USER, created_at=self.now, updated_at=self.now)

    def test_invalid_sender(self):
        with pytest.raises(ValidationError):
            MessageModel(chat_id="chat_1", sender="wrongsender", content="hello", created_at=self.now, updated_at=self.now)

    def test_invalid_classification(self):
        with pytest.raises(ValidationError):
            MessageModel(chat_id="chat_1", sender=SenderType.USER, content="hello", classification="wrongclass", created_at=self.now, updated_at=self.now)
