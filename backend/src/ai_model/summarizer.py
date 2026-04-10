"""
summarizer.py

Generoi tiivistelmän keskustelusta, kun luokittelija on todennut
käyttäjän viestin vaativan ammattilaisen tarkistusta (NEEDS_REVIEW).

"""

from config import settings
import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


# LLM tiivistämiseen (matala temperature tarkkuuden vuoksi)
summarizer_llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash-lite',
    temperature=0,
    max_tokens=800,
    google_api_key=settings.GOOGLE_API_KEY
)

def _format_history(messages) -> str:
    """Muotoilee LangChain-viestit luettavaan muotoon."""
    formatted = []
    for msg in messages:
        if hasattr(msg, 'type') and hasattr(msg, 'content'):
            # LangChain message object
            role = "Patient" if msg.type == "human" else "Chatbot"
            formatted.append(f"{role}: {msg.content}")
        elif isinstance(msg, dict):
            sender = msg.get("sender") or msg.get("type", "")
            role = "Patient" if sender in ("user", "human") else "Chatbot"
            formatted.append(f"{role}: {msg.get('content', '')}")
    return "\n".join(formatted) if formatted else "No conversation history available."


def _format_user_data(user_data: Optional[dict]) -> str:
    """Muotoilee käyttäjädatan luettavaan muotoon."""
    if not user_data:
        return "No patient data available."

    parts = []
    for key, value in user_data.items():
        if key == "_id":
            continue
        parts.append(f"- {key}: {value}")
    return "\n".join(parts) if parts else "No patient data available."


PROFESSIONAL_SUMMARY_PROMPT = """You are a medical conversation summarizer. A patient has been chatting with a healthcare chatbot, and the system has flagged the conversation for professional review.

Create a concise summary of the conversation for a healthcare professional to review.

IMPORTANT: Detect the language of the conversation (Finnish or English) and write the summary in the SAME language.

CONVERSATION HISTORY:
{history}

PATIENT DATA:
{user_data}

Write a concise summary covering:
1. What the patient asked about or was concerned about
2. Key medically relevant details from the conversation
3. Why this conversation needs professional review

Keep the summary focused and actionable for the reviewing professional."""


async def generate_summary_for_professional(
    messages: list,
    user_data: dict | None = None,
) -> dict:
    """
    Generoi tiivistelmän ammattilaisnäkymää varten lennossa.

    Kutsutaan GET /professional/chats/{chat_id} -endpointissa.
    Ei tallenna mitään MongoDB:hen.

    Args:
        messages: Viestilista (MongoDB dict-muodossa, kentät "type" ja "content").
        user_data: Potilaan taustatiedot (MongoDB-dokumentti tai None).

    Returns:
        dict: patient_context, chat_summary, draft_response, requires_approval
    """
    patient_context = _format_user_data(user_data)
    history_text = _format_history(messages)

    try:
        prompt = PROFESSIONAL_SUMMARY_PROMPT.format(
            history=history_text,
            user_data=patient_context,
        )
        response = await summarizer_llm.ainvoke(prompt)
        chat_summary = response.content.strip()
    except Exception as e:
        logger.error(f"Professional summary generation failed, using fallback: {e}")
        chat_summary = (
            f"[Automaattinen tiivistelmä – LLM ei saatavilla / Automatic summary – LLM unavailable]\n\n"
            f"Viestien määrä / Conversation length: {len(messages)}\n"
            f"Potilasdata saatavilla / Patient data available: {'Kyllä / Yes' if user_data else 'Ei / No'}"
        )

    # Haetaan viimeinen potilaan viesti ja generoidaan draft RAG-vastauksella
    draft_response = ""
    last_human_msg = ""
    for msg in reversed(messages):
        sender = msg.get("sender") or msg.get("type", "")
        if sender in ("user", "human"):
            last_human_msg = msg.get("content", "")
            break

    if last_human_msg:
        if chat_summary:
            draft_prompt = (
                f"[Conversation summary: {chat_summary}]\n\n"
                f"[Patient info: {patient_context}]\n\n"
                f"Patient's latest message: {last_human_msg}"
            )
        else:
            draft_prompt = last_human_msg
        try:
            from ai_model import rag_cloud, utils
            raw_draft = await rag_cloud.generate_draft_response(draft_prompt)
            draft_response = utils.formatGeminiResponse(raw_draft)
        except Exception as e:
            logger.error(f"Draft response generation failed: {e}")
            draft_response = ""

    return {
        "patient_context": patient_context,
        "chat_summary": chat_summary,
        "draft_response": draft_response,
        "requires_approval": True,
    }


CHAT_TITLE_PROMPT = """Generate an extremely concise title (3-6 words) for a health chat conversation.
Detect the language of the message (Finnish or English) and write the title in the SAME language.
Do NOT use quotes, punctuation marks, or any surrounding text — output ONLY the title words.

User's first message: {message}

Title:"""


async def generate_chat_title(first_message: str) -> str | None:
    """
    Generates a short 3-6 word title for a chat based on the user's first message.
    Returns None on failure. Never raises.
    """
    try:
        prompt = CHAT_TITLE_PROMPT.format(message=first_message[:400])
        response = await summarizer_llm.ainvoke(prompt)
        title = response.content.strip().strip('"\'')
        return title[:80] if title else None
    except Exception as e:
        logger.error(f"Chat title generation failed: {e}")
        return None
