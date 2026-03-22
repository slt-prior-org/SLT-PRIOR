from fastapi import HTTPException, APIRouter, Request, Depends
from typing import List, Dict, Any
from ai_model import rag_cloud
from ai_model import utils
from ai_model.classifier import classify_question, Classification
from ai_model.rag_cloud import get_guideline_excerpt, translate_excerpt
from ai_model.emergency import detect_emergency
from bson import ObjectId
from database.db import users_collection, chats_collection
from database.models import ChatStatus, SendMessageRequest, ChatReplyResponse, ChatDetailResponse, ChatSummaryItem
from routes.auth import get_current_user
from utils.chat_utils import get_chat_summaries, get_chats_with_messages
from datetime import datetime


router = APIRouter()

@router.get("/", response_model=List[ChatSummaryItem])
async def get_chats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns all chat sessions belonging to the authenticated user.
    The user is identified from the JWT token via the get_current_user dependency.
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

    # 1) Hätätilanteen tunnistus
    emergency = detect_emergency(user_message)
    if emergency:
        return {
            "reply": "",
            "classification": Classification.EMERGENCY,
        }

    # 2) Haetaan käyttäjädata, jos user_id on annettu
    user_data = None
    if user_id:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format.")
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])
            user_data = user_doc

    # 3) Kerätään conversation history RAG-muistista
    # Huom: Tämä muokataan hakemaan mongoDB:stä, mutta toistaiseksi käytetään RAG-muistin viestejä?
    conversation_history = [
        {"sender": "user" if msg.type == "human" else "bot", "content": msg.content}
        for msg in rag_cloud.memory.messages
    ]

    # 4) Luokitellaan kysymys ennen RAG-kutsua
    classification_result = await classify_question(
        question=user_message,
        user_data=user_data,
        is_logged_in=logged_in,
        conversation_history=conversation_history if conversation_history else None,
    )

    # 5) NEEDS_REVIEW – palataan heti, ei RAG-kutsua
    if classification_result.classification == Classification.NEEDS_REVIEW:
        _FINNISH_WORDS = {
            "sopiiko", "minulle", "minun", "kanssa", "liikunta", "raskas",
            "harrastaa", "onko", "voiko", "voisiko", "tarvitsen", "tarvitsee",
            "lopettaa", "aloittaa", "vaarallista", "turvallista", "verenpaine",
            "sydansairaus", "lihavuus", "laihduttaa", "ruokavalio",
        }
        is_finnish = (
            any(c in user_message for c in "äöåÄÖÅ")
            or any(w in user_message.lower().split() for w in _FINNISH_WORDS)
        )
        if is_finnish:
            excerpt_query = f"{user_message} hoitosuositus suomalainen ohje"
        else:
            excerpt_query = f"{user_message} care guideline Finnish recommendation"
        excerpt_data = await get_guideline_excerpt(excerpt_query, score_threshold=0.60)

        if excerpt_data:
            excerpt_is_finnish = any(c in excerpt_data["text"] for c in "äöåÄÖÅ")
            print(f"DEBUG excerpt_is_finnish={excerpt_is_finnish}, is_finnish={is_finnish}, text[:80]={excerpt_data['text'][:80]!r}")
            if is_finnish and not excerpt_is_finnish:
                excerpt_data["text"] = await translate_excerpt(excerpt_data["text"], target="fi")
            elif not is_finnish and excerpt_is_finnish:
                excerpt_data["text"] = await translate_excerpt(excerpt_data["text"], target="en")
            # Osuva excerpt löytyi → käyttäjä vahvistaa tarpeen (teksti haetaan frontendin locale-tiedostoista)
            reply = ""
            return {
                "reply": reply,
                "requires_confirmation": True,
                "classification": Classification.NEEDS_REVIEW,
                "classification_reasoning": classification_result.reasoning,
                "guideline_excerpt": excerpt_data["text"],
                "guideline_source": excerpt_data["source"],
            }
        else:
            # Ei osuvaa excerptia → välitetään heti ammattilaiselle (teksti haetaan frontendin locale-tiedostoista)
            return {
                "reply": "",
                "requires_professional": True,
                "classification": Classification.NEEDS_REVIEW,
                "classification_reasoning": classification_result.reasoning,
            }

    # 6) Rakennetaan prompt käyttäjädatan perusteella (jos SAFE)
    if logged_in and user_data and user_data.get("patient_info"):
        patient_info = user_data["patient_info"]
        prompt = f"{user_message}\n\nPatient info:\n{patient_info}"
    else:
        prompt = user_message

    # 7) Kutsutaan RAG-mallia
    try:
        raw_response = await rag_cloud.get_rag_response(prompt)
        formatted_text = utils.formatGeminiResponse(raw_response)
    except Exception as e:
        import traceback
        traceback.print_exc()   # Näyttää tarkemman syyn konsolissa
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "reply": formatted_text,
        "classification": Classification.SAFE,
    }

@router.post("/chat", response_model=ChatDetailResponse)
async def create_chat(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Create a new chat document in the database.
    Use the authenticated users info.
    Return the created chat object with an empty messages list.
    """

    new_chat = {
        "user_id": ObjectId(current_user["_id"]),
        "status": ChatStatus.OPEN,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
        }

    res = await chats_collection.insert_one(new_chat)

    return ChatDetailResponse(
        id=str(res.inserted_id),
        user_id=current_user["_id"],
        status=ChatStatus.OPEN,
        assigned_professional_id=None,
        created_at=new_chat["created_at"],
        updated_at=new_chat["updated_at"],
        messages=[]
    )



@router.get("/{chatId}", response_model=ChatDetailResponse)
async def get_chat_id(chatId: str ,current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get a chat details by {chatId}.
    Depends on get_current_user.
    Return the chat with all of the messages included.
    """

    # Reject invalid ObjectId format before reaching for database
    if not ObjectId.is_valid(chatId):
        raise HTTPException(400, "Invalid chat_id")

    chats = await get_chats_with_messages({"_id": ObjectId(chatId)})

    # Check if chat exists
    if not chats:
        raise HTTPException(404, "Chat not found")

    chat_owner = chats[0]["user_id"]
    logged_in_user = current_user["_id"]
    
    # Check if chat belongs to someone else
    if chat_owner != logged_in_user:
        raise HTTPException(403, "Forbidden")

    # Unpack chat document into ChatDetailResponse
    return ChatDetailResponse(**chats[0])