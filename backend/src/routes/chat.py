from fastapi import HTTPException, APIRouter, Request
from ai_model import rag_cloud
from ai_model import utils
from bson import ObjectId
from database.db import users_collection
from database.models import SendMessageRequest, ChatReplyResponse

router = APIRouter()

@router.post("/send", response_model=ChatReplyResponse)
async def send_message(body: SendMessageRequest, request: Request):
    """
    1) Lukee frontendiltä tulevan 'message' ja (optionaalisen) 'user_id' -kentän.
    2) Jos user_id on annettu ja kelvollinen, hakee käyttäjädatan MongoDB:stä.
    3) Yhdistää käyttäjädatan promtiin ja kutsuu RAG-mallia.
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