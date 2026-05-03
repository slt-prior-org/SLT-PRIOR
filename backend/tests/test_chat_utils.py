import pytest
import sys
import os
from datetime import datetime
import pytest_asyncio
from unittest.mock import patch, AsyncMock 

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.chat_utils import _normalize_sources, _normalize_message_doc, serialize_datetime, get_chat, get_chat_messages, save_chat_message
from database.models import SenderType, Classification

pytestmark = pytest.mark.unit

class TestNormalizeSources:
    def test_valid_list_of_dicts(self):
        list_of_dicts = [
            {"key1": "value1"},
            {"key2": "value2"},
            {"key3": "value3"}
        ]
        normalized = _normalize_sources(list_of_dicts)
        assert normalized == list_of_dicts

    def test_string_input(self):
        assert [] == _normalize_sources("should return empty list")

    def test_dict_input(self):
        assert [] == _normalize_sources({"key": "should return empty list"})

    def test_mixed_input(self):
        mixed = [{"key": "value"}, "string", 42]
        res = _normalize_sources(mixed)
        assert res == [{"key": "value"}]

    def test_empty_list_input(self):
        assert [] == _normalize_sources([])


class TestSerializeDatetime:
    def test_datetime_returns_iso_string(self):
        # create a datetime object, call serialize_datetime, assert result is a string in ISO format
        date_object = datetime.now()
        res = serialize_datetime(date_object)
        assert isinstance(res, str)
        
    def test_non_datetime_raises_type_error(self):
        # pass a string to serialize_datetime, expect TypeError
        with pytest.raises(TypeError):
            serialize_datetime("this is a string")


class TestNormalizeMessageDoc:
    # Create a mock mongoDB message dict
    message = {
        "_id": "abc123",
        "chat_id": "chat456",
        "sources": []
        }
      
    def test_id_field_replaces_underscore_id(self):
        # create a message dict with "_id", call _normalize_message_doc, assert "id" exists and "_id" does not
        normalized = _normalize_message_doc(self.message)
        assert normalized["id"] == "abc123"
        assert "_id" not in normalized

    def test_chat_id_is_string(self):
        # assert normalized["chat_id"] is a str
        normalized = _normalize_message_doc(self.message)
        assert isinstance(normalized["chat_id"], str)

    def test_sources_is_normalized(self):
        # pass a message with no sources, assert normalized["sources"] == []
        assert _normalize_message_doc(self.message)["sources"] == []


class TestGetChat:
    
    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_id(self):
        res = await get_chat("not_a_valid_chat_id")
        assert res is None

    @patch("utils.chat_utils.chats_collection")
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_collection):
        # Set up the mock to simulate empty DB result
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = []
        mock_collection.aggregate = AsyncMock(return_value = mock_cursor)

        result = await get_chat("507f1f77bcf86cd799439011")  # valid ObjectId format
        assert result is None

    @patch("utils.chat_utils.chats_collection")
    @pytest.mark.asyncio
    async def test_returns_chat_when_found(self, mock_collection):
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [{"id": "507f1f77bcf86cd799439011", "status": "open"}]
        mock_collection.aggregate = AsyncMock(return_value = mock_cursor)

        res = await get_chat("507f1f77bcf86cd799439011")
        assert res == {"id": "507f1f77bcf86cd799439011", "status": "open"}


class TestGetChatMessages:
    VALID_CHAT_ID = "507f1f77bcf86cd799439011"

    @patch("utils.chat_utils.messages_collection")
    @pytest.mark.asyncio
    async def test_returns_messages_for_chat(self, mock_collection):
        from bson import ObjectId
        raw_message = {
            "_id": ObjectId("507f191e810c19729de860ea"),
            "chat_id": ObjectId(self.VALID_CHAT_ID),
            "sender": "user",
            "content": "hello",
            "classification": "safe",
            "flagged_for_human": False,
            "sources": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [raw_message]
        mock_collection.find.return_value.sort.return_value = mock_cursor

        result = await get_chat_messages(self.VALID_CHAT_ID)
        assert len(result) == 1
        assert result[0]["content"] == "hello"
        assert "id" in result[0]
        assert "_id" not in result[0]

    @patch("utils.chat_utils.messages_collection")
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_messages(self, mock_collection):
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = []
        mock_collection.find.return_value.sort.return_value = mock_cursor

        result = await get_chat_messages(self.VALID_CHAT_ID)
        assert result == []


class TestSaveChatMessage:
    VALID_CHAT_ID = "507f1f77bcf86cd799439011"

    @patch("utils.chat_utils.messages_collection")
    @pytest.mark.asyncio
    async def test_saves_message_and_returns_response(self, mock_collection):
        from bson import ObjectId
        inserted_id = ObjectId("507f191e810c19729de860ea")
        mock_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=inserted_id))

        result = await save_chat_message(
            chat_id=self.VALID_CHAT_ID,
            sender=SenderType.USER,
            content="test message",
        )
        assert result.content == "test message"
        assert result.sender == SenderType.USER
        assert result.classification == Classification.SAFE

    @patch("utils.chat_utils.messages_collection")
    @pytest.mark.asyncio
    async def test_default_classification_is_safe(self, mock_collection):
        from bson import ObjectId
        mock_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=ObjectId()))

        result = await save_chat_message(
            chat_id=self.VALID_CHAT_ID,
            sender=SenderType.BOT,
            content="bot reply",
        )
        assert result.classification == Classification.SAFE