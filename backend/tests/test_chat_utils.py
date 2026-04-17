import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.chat_utils import _normalize_sources, _normalize_message_doc, serialize_datetime

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