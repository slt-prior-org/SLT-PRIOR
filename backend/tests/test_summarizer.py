"""
Yksikkötestit tiivistelmän generoinnille (summarizer.py).
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Lisää src-hakemisto importteihin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Mock langchain_google_genai jos sitä ei ole asennettu (lokaalissa ympäristössä)
try:
    import langchain_google_genai  # noqa: F401
except ModuleNotFoundError:
    mock_module = MagicMock()
    sys.modules["langchain_google_genai"] = mock_module

# Mock rag_cloud ja utils, joita summarizer importtaa lennossa
# (rag_cloud vaatii google.cloud -riippuvuuden jota ei ole lokaalissa ympäristössä)
mock_rag_cloud = MagicMock()
mock_rag_cloud.get_rag_response = AsyncMock(return_value={"answer": "", "sources": []})
sys.modules.setdefault("ai_model.rag_cloud", mock_rag_cloud)

mock_utils = MagicMock()
mock_utils.formatGeminiResponse = MagicMock(return_value="")
sys.modules.setdefault("ai_model.utils", mock_utils)

from ai_model.summarizer import (
    generate_summary_for_professional,
    _format_history,
    _format_user_data,
)


# ---------- _format_history ----------

class TestFormatHistory:
    def test_langchain_messages(self):
        """Testaa LangChain-viestiobjektien muotoilua."""
        msg1 = MagicMock()
        msg1.type = "human"
        msg1.content = "Hei, minulla on kysymys"
        msg2 = MagicMock()
        msg2.type = "ai"
        msg2.content = "Miten voin auttaa?"

        result = _format_history([msg1, msg2])
        assert "Patient: Hei, minulla on kysymys" in result
        assert "Chatbot: Miten voin auttaa?" in result

    def test_dict_messages(self):
        """Testaa dict-muotoisten viestien muotoilua."""
        messages = [
            {"type": "human", "content": "What is CAD?"},
            {"type": "ai", "content": "CAD stands for..."}
        ]
        result = _format_history(messages)
        assert "Patient: What is CAD?" in result
        assert "Chatbot: CAD stands for..." in result

    def test_empty_history(self):
        result = _format_history([])
        assert "No conversation history" in result


# ---------- _format_user_data ----------

class TestFormatUserData:
    def test_with_data(self):
        data = {"weight": 85, "conditions": ["hypertension"]}
        result = _format_user_data(data)
        assert "weight: 85" in result
        assert "conditions:" in result

    def test_none_data(self):
        result = _format_user_data(None)
        assert "No patient data" in result

    def test_skips_id_field(self):
        data = {"_id": "abc123", "weight": 85}
        result = _format_user_data(data)
        assert "_id" not in result
        assert "weight: 85" in result

    def test_empty_dict(self):
        result = _format_user_data({})
        assert "No patient data" in result


# ---------- generate_summary_for_professional ----------

class TestGenerateSummaryForProfessional:
    @pytest.mark.asyncio
    async def test_successful_generation(self):
        """Testaa onnistunutta ammattilaisen tiivistelmän generointia."""
        mock_response = MagicMock()
        mock_response.content = "Patient asked about blood pressure medication."

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "ai_model.summarizer.summarizer_llm",
            mock_llm,
        ), patch(
            "ai_model.rag_cloud.get_rag_response",
            new_callable=AsyncMock,
            return_value={"answer": "Raw RAG draft response", "sources": []},
        ), patch(
            "ai_model.utils.formatGeminiResponse",
            return_value="Formatted RAG draft response",
        ):
            messages = [
                {"type": "human", "content": "Onko verenpaineeni liian korkea?"},
                {"type": "ai", "content": "En voi arvioida sitä."},
            ]
            result = await generate_summary_for_professional(
                messages=messages,
                user_data={"weight": 85, "conditions": ["hypertension"]},
            )

        assert isinstance(result, dict)
        assert result["chat_summary"] == "Patient asked about blood pressure medication."
        assert result["draft_response"] == "Formatted RAG draft response"
        assert result["draft_sources"] == []
        assert result["requires_approval"] is True
        assert "weight: 85" in result["patient_context"]

    @pytest.mark.asyncio
    async def test_draft_uses_last_human_message(self):
        """Testaa että draft generoidaan viimeisestä potilaan viestistä."""
        mock_response = MagicMock()
        mock_response.content = "Summary."

        mock_draft = AsyncMock(return_value={"answer": "Draft from last message", "sources": []})

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "ai_model.summarizer.summarizer_llm",
            mock_llm,
        ), patch(
            "ai_model.rag_cloud.get_rag_response",
            mock_draft,
        ), patch(
            "ai_model.utils.formatGeminiResponse",
            return_value="Formatted draft",
        ):
            messages = [
                {"type": "human", "content": "Ensimmäinen viesti"},
                {"type": "ai", "content": "Vastaus"},
                {"type": "human", "content": "Toinen viesti"},
            ]
            result = await generate_summary_for_professional(
                messages=messages,
            )

        # Varmistetaan että RAG-kutsua kutsuttiin yhdistetyllä promptilla
        mock_draft.assert_called_once()
        call_arg = mock_draft.call_args[0][0]
        assert "Toinen viesti" in call_arg
        assert "Summary." in call_arg  # chat_summary on mukana promptissa
        assert result["draft_response"] == "Formatted draft"
        assert result["draft_sources"] == []

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """Testaa fallback-mekanismia, kun LLM epäonnistuu."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API error"))

        with patch(
            "ai_model.summarizer.summarizer_llm",
            mock_llm,
        ), patch(
            "ai_model.rag_cloud.get_rag_response",
            new_callable=AsyncMock,
            return_value={"answer": "draft text", "sources": []},
        ), patch(
            "ai_model.utils.formatGeminiResponse",
            return_value="formatted draft",
        ):
            messages = [{"type": "human", "content": "Help me"}]
            result = await generate_summary_for_professional(
                messages=messages,
                user_data=None,
            )

        assert "Automatic summary" in result["chat_summary"]
        assert "LLM unavailable" in result["chat_summary"]
        assert result["requires_approval"] is True
        assert "No patient data" in result["patient_context"]

    @pytest.mark.asyncio
    async def test_draft_fallback_on_rag_failure(self):
        """Testaa että draft jää tyhjäksi, kun RAG-kutsu epäonnistuu."""
        mock_response = MagicMock()
        mock_response.content = "Summary."

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "ai_model.summarizer.summarizer_llm",
            mock_llm,
        ), patch(
            "ai_model.rag_cloud.get_rag_response",
            new_callable=AsyncMock,
            side_effect=Exception("RAG error"),
        ):
            messages = [{"type": "human", "content": "Help me"}]
            result = await generate_summary_for_professional(
                messages=messages,
            )

        assert result["draft_response"] == ""
        assert result["draft_sources"] == []

    @pytest.mark.asyncio
    async def test_without_user_data(self):
        """Testaa generointia ilman potilastietoja."""
        mock_response = MagicMock()
        mock_response.content = "Summary text."

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "ai_model.summarizer.summarizer_llm",
            mock_llm,
        ), patch(
            "ai_model.rag_cloud.get_rag_response",
            new_callable=AsyncMock,
            return_value={"answer": "", "sources": []},
        ), patch(
            "ai_model.utils.formatGeminiResponse",
            return_value="",
        ):
            result = await generate_summary_for_professional(
                messages=[],
                user_data=None,
            )

        assert result["patient_context"] == "No patient data available."
        assert result["chat_summary"] == "Summary text."
        assert result["draft_response"] == ""
        assert result["draft_sources"] == []
        assert result["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_returns_all_required_keys(self):
        """Testaa että palautettu dict sisältää kaikki vaaditut kentät."""
        mock_response = MagicMock()
        mock_response.content = "Summary."

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "ai_model.summarizer.summarizer_llm",
            mock_llm,
        ), patch(
            "ai_model.rag_cloud.generate_draft_response",
            new_callable=AsyncMock,
            return_value="draft",
        ), patch(
            "ai_model.utils.formatGeminiResponse",
            return_value="formatted draft",
        ):
            result = await generate_summary_for_professional(
                messages=[],
                user_data=None,
            )

        expected_keys = {"patient_context", "chat_summary", "draft_response",
                          "draft_sources", "requires_approval"}
        assert set(result.keys()) == expected_keys
