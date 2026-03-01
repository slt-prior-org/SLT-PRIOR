from fastapi import HTTPException, APIRouter, Request
from ai_model import rag_cloud
from ai_model import utils
from ai_model.classifier import classify_question, Classification
from ai_model.emergency import detect_emergency
from bson import ObjectId
from database.db import users_collection
from database.models import SendMessageRequest

router = APIRouter()

@router.post("/send")
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
            "reply": emergency.emergency_message_en,
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
        safe_message = (
            "Kysymyksesi saattaa vaatia ammattilaisen arviointia. "
            "Vastauksesi on tallennettu ja lähetetään tarkistettavaksi.<br><br>"
            "Your question may require professional review. "
            "Your response has been saved and will be sent for review."
        )
        return {
            "reply": safe_message,
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
