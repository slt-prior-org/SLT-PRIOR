from fastapi import HTTPException, APIRouter, Request, Depends
from typing import List, Dict, Any
from ai_model import rag_cloud
from ai_model import utils
from bson import ObjectId
from database.db import users_collection, chats_collection
from database.models import ChatStatus, SendMessageRequest, ChatReplyResponse, ChatDetailResponse, ChatModel, ChatSummaryItem
from routes.auth import get_current_user
from datetime import datetime


router = APIRouter()

@router.get("/", response_model=List[ChatSummaryItem])
async def get_chats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns all chat sessions belonging to the authenticated user.
    The user is identified from the JWT token via the get_current_user dependency.
    """
    user_id = current_user["_id"]
    chats = await chats_collection.find({"user_id": user_id}).to_list(None)
    return [
        {
            "id": str(chat["_id"]),
            "status": chat["status"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"],
        }
        for chat in chats
    ]


@router.post("/send", response_model=ChatReplyResponse)
async def send_message(body: SendMessageRequest, request: Request):
    """
    1) Lukee frontendiltä tulevan 'message' ja (optionaalisen) 'user_id' -kentän.
    2) Jos user_id on annettu ja kelvollinen, hakee käyttäjädatan MongoDB:stä.
    3) Yhdistää käyttäjädatan promptiin ja kutsuu RAG-mallia.
    """

    logged_in = request.app.state.logged_in

    user_message = body.message
    user_id = request.app.state.current_user_id

    # 1) Haetaan käyttäjädata, jos user_id on annettu
    user_data = None
    if user_id:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format.")
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])  # Muunnetaan _id stringiksi
            user_data = user_doc

    # 2) Rakennetaan prompt, jossa lisätään käyttäjädata mukaan
    if logged_in and user_data and user_data.get("patient_info"):
        patient_info = user_data["patient_info"]
        prompt = f"{user_message}\n\nPatient info:\n{patient_info}"
    else:
        prompt = user_message

    # 3) Kutsutaan RAG-mallia
    try:
        raw_response = await rag_cloud.get_rag_response(prompt)
        formatted_text = utils.formatGeminiResponse(raw_response)
        return {"reply": formatted_text}
    except Exception as e:
        import traceback
        traceback.print_exc()  # Näyttää tarkemman syyn konsolissa
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/chat", response_model=ChatSummaryItem)
async def create_chat(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Create a new chat document in the database
    Use the authenticated users info
    Return the created chat object
    """
    
    new_chat = {
        "user_id": str(current_user["_id"]),
        "status": ChatStatus.OPEN,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
        }
    
    res = await chats_collection.insert_one(new_chat)
    new_chat["_id"] = str(res.inserted_id)

    return {
            "id": str(new_chat["_id"]),
            "status": new_chat["status"],
            "created_at": new_chat["created_at"],
            "updated_at": new_chat["updated_at"],
        }