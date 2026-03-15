from datetime import datetime
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from ai_model import rag_cloud, utils
from ai_model.classifier import classify_question, Classification as AiClassification
from ai_model.emergency import detect_emergency
from database.db import chats_collection, users_collection
from database.models import (
    ChatDetailResponse,
    ChatReplyResponse,
    ChatStatus,
    ChatSummaryItem,
    Classification as DbClassification,
    SendChatMessageResponse,
    SendMessageRequest,
    SenderType,
)
from routes.auth import get_current_user
from utils.chat_utils import (
    get_chat_messages,
    get_chat_summaries,
    get_chats_with_messages,
    save_chat_message,
    touch_chat,
)


router = APIRouter()


async def _get_owned_chat_or_404(chat_id: str, current_user: Dict[str, Any]) -> dict:
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(400, "Invalid chat_id")

    chat = await chats_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(404, "Chat not found")

    if str(chat["user_id"]) != current_user["_id"]:
        raise HTTPException(403, "Forbidden")

    return chat


@router.get("/", response_model=List[ChatSummaryItem])
async def get_chats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Palauttaa kaikki tunnistautuneen käyttäjän chatit.
    Käyttäjä tunnistetaan JWT-tokenista get_current_user-riippuvuuden avulla.
    """
    user_id = current_user["_id"]
    return await get_chat_summaries({"user_id": ObjectId(user_id)})


@router.post("/send", response_model=ChatReplyResponse)
async def send_message(body: SendMessageRequest, request: Request):
    """
    1) Hätätilanteen tunnistus (detect_emergency) – palautetaan välittömästi.
    2) Haetaan käyttäjädata MongoDB:stä.
    3) Kerätään conversation history RAG-muistista.
    4) Luokitellaan kysymys (classify_question) ennen RAG-kutsua.
    5) Rakennetaan prompt käyttäjädatan perusteella.
    6) Kutsutaan RAG-mallia.
    7) SAFE → palautetaan reply + classification.
    8) NEEDS_REVIEW → palautetaan turvallinen viesti + draft_response + classification_reasoning.
    """

    logged_in = request.app.state.logged_in
    user_message = body.message
    user_id = request.app.state.current_user_id

    emergency = detect_emergency(user_message)
    if emergency:
        return {
            "reply": emergency.emergency_message_en,
            "classification": AiClassification.EMERGENCY,
        }

    user_data = None
    if user_id:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format.")
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])
            user_data = user_doc

    conversation_history = [
        {"sender": "user" if msg.type == "human" else "bot", "content": msg.content}
        for msg in rag_cloud.memory.messages
    ]

    classification_result = await classify_question(
        question=user_message,
        user_data=user_data,
        is_logged_in=logged_in,
        conversation_history=conversation_history if conversation_history else None,
    )

    if classification_result.classification == AiClassification.NEEDS_REVIEW:
        safe_message = (
            "Tämä aihe liittyy henkilökohtaiseen "
            "terveysarviointiin, johon en voi antaa vastausta. Keskustelusi "
            "on välitetty ammattilaiselle arvioitavaksi."
            "<br><br>"
            "This topic relates to a personal "
            "health assessment that I cannot answer. Your conversation has been "
            "forwarded to a professional for review."
        )
        return {
            "reply": safe_message,
            "requires_professional": True,
            "classification": AiClassification.NEEDS_REVIEW,
            "classification_reasoning": classification_result.reasoning,
        }

    if logged_in and user_data and user_data.get("patient_info"):
        patient_info = user_data["patient_info"]
        prompt = f"{user_message}\n\nPatient info:\n{patient_info}"
    else:
        prompt = user_message

    try:
        raw_response = await rag_cloud.get_rag_response(prompt)
        formatted_text = utils.formatGeminiResponse(raw_response)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "reply": formatted_text,
        "classification": AiClassification.SAFE,
    }


@router.post("/chat", response_model=ChatDetailResponse)
async def create_chat(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Luo tietokantaan uuden chat-dokumentin.
    Käyttää tunnistautuneen käyttäjän tietoja.
    Palauttaa luodun chatin tyhjällä viestilistalla.
    """

    new_chat = {
        "user_id": ObjectId(current_user["_id"]),
        "status": ChatStatus.OPEN,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    res = await chats_collection.insert_one(new_chat)

    return ChatDetailResponse(
        id=str(res.inserted_id),
        user_id=current_user["_id"],
        status=ChatStatus.OPEN,
        assigned_professional_id=None,
        created_at=new_chat["created_at"],
        updated_at=new_chat["updated_at"],
        messages=[],
    )


@router.post("/{chatId}", response_model=SendChatMessageResponse)
async def send_message_to_chat(
    chatId: str,
    body: SendMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Chat-kohtainen viestinlähetysreitti tunnistautuneelle käyttäjälle.
    Tallentaa käyttäjän ja botin viestit MongoDB:hen ja varmistaa,
    että chat kuuluu nykyiselle käyttäjälle. RAG- ja luokittelukäyttäytyminen
    pidetään toistaiseksi yhteensopivana vanhan /send-reitin kanssa.
    """

    chat = await _get_owned_chat_or_404(chatId, current_user)
    existing_messages = await get_chat_messages(chatId)

    conversation_history = [
        {"sender": message["sender"], "content": message["content"]}
        for message in existing_messages
    ]

    user_message = body.message
    user_data = current_user
    logged_in = True

    emergency = detect_emergency(user_message)
    if emergency:
        saved_user_message = await save_chat_message(
            chatId,
            SenderType.USER,
            user_message,
            classification=DbClassification.EMERGENCY,
        )
        saved_bot_message = await save_chat_message(
            chatId,
            SenderType.BOT,
            emergency.emergency_message_en,
            classification=DbClassification.EMERGENCY,
        )
        await touch_chat(chatId)
        return SendChatMessageResponse(
            userMessage=saved_user_message,
            botMessage=saved_bot_message,
        )

    classification_result = await classify_question(
        question=user_message,
        user_data=user_data,
        is_logged_in=logged_in,
        conversation_history=conversation_history if conversation_history else None,
    )

    if classification_result.classification == AiClassification.NEEDS_REVIEW:
        safe_message = (
            "Tämä aihe liittyy henkilökohtaiseen "
            "terveysarviointiin, johon en voi antaa vastausta. Keskustelusi "
            "on välitetty ammattilaiselle arvioitavaksi."
            "<br><br>"
            "This topic relates to a personal "
            "health assessment that I cannot answer. Your conversation has been "
            "forwarded to a professional for review."
        )

        saved_user_message = await save_chat_message(
            chatId,
            SenderType.USER,
            user_message,
            classification=DbClassification.NEEDS_REVIEW,
            flagged_for_human=True,
        )
        saved_bot_message = await save_chat_message(
            chatId,
            SenderType.BOT,
            safe_message,
            classification=DbClassification.NEEDS_REVIEW,
        )
        await touch_chat(chatId, status=ChatStatus.WAITING)
        return SendChatMessageResponse(
            userMessage=saved_user_message,
            botMessage=saved_bot_message,
            requires_professional=True,
            classification_reasoning=classification_result.reasoning,
        )

    if logged_in and user_data.get("patient_info"):
        patient_info = user_data["patient_info"]
        prompt = f"{user_message}\n\nPatient info:\n{patient_info}"
    else:
        prompt = user_message

    saved_user_message = await save_chat_message(
        chatId,
        SenderType.USER,
        user_message,
        classification=DbClassification.SAFE,
    )

    try:
        raw_response = await rag_cloud.get_rag_response(
            prompt,
            save_to_memory=False,
            chat_history=conversation_history,
        )
        formatted_text = utils.formatGeminiResponse(raw_response)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    saved_bot_message = await save_chat_message(
        chatId,
        SenderType.BOT,
        formatted_text,
        classification=DbClassification.SAFE,
    )
    await touch_chat(chat["_id"])

    return SendChatMessageResponse(
        userMessage=saved_user_message,
        botMessage=saved_bot_message,
    )


@router.get("/{chatId}", response_model=ChatDetailResponse)
async def get_chat_id(chatId: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Hakee yksittäisen chatin tiedot chatId:n perusteella.
    Käyttää get_current_user-riippuvuutta.
    Palauttaa chatin sekä kaikki siihen kuuluvat viestit.
    """

    if not ObjectId.is_valid(chatId):
        raise HTTPException(400, "Invalid chat_id")

    chats = await get_chats_with_messages({"_id": ObjectId(chatId)})

    if not chats:
        raise HTTPException(404, "Chat not found")

    chat_owner = chats[0]["user_id"]
    logged_in_user = current_user["_id"]

    if chat_owner != logged_in_user:
        raise HTTPException(403, "Forbidden")

    return ChatDetailResponse(**chats[0])
