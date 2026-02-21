from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Haetaan kirjautuneen käyttäjän tiedot ja kirjautumisen tila
from routes.users import router as user_router, current_user_id, logged_in

from ai_model import rag_cloud
from ai_model import utils

from bson import ObjectId
from uuid import uuid4

from database.db import users_collection
from database.chat_store import get_recent_messages, save_message


app = FastAPI()

# Alustetaan globaalien muuttujien tila
app.state.logged_in = False
app.state.current_user_id = None
app.state.current_user_data = None

# CORS (Allow frontend to communicate with backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello from FastAPI!"}


@app.post("/api/send")
async def send_message(payload: dict):
    """
    1) Lukee frontendiltä tulevan 'message' ja (optionaalisen) 'chat_id' -kentän.
    2) Hakee keskusteluhistorian MongoDB:stä user_id + chat_id perusteella.
    3) Tallentaa user-viestin MongoDB:hen.
    4) (Optionaalisesti) hakee patient_info jos logged_in ja user_id on valid ObjectId.
    5) Kutsuu RAG-mallia (historia mukana).
    6) Tallentaa bot-viestin MongoDB:hen.
    7) Palauttaa reply + chat_id.
    """
    logged_in_state = app.state.logged_in

    user_message = payload.get("message")
    chat_id = payload.get("chat_id") or str(uuid4())

    user_id = app.state.current_user_id or "guest"

    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required.")

    # 1) Hae viimeisimmät viestit tästä chatista
    history_docs = await get_recent_messages(user_id=user_id, chat_id=chat_id, limit=20)

    # 2) Tallenna user-viesti (T-yhteensopiva sender)
    await save_message(user_id=user_id, chat_id=chat_id, sender="user", content=user_message)

    # 3) Rakennetaan prompt (patient_info mukaan vain jos logged_in ja user_id valid)
    prompt = user_message

    user_data = None
    if logged_in_state and user_id != "guest" and ObjectId.is_valid(user_id):
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])
            user_data = user_doc

    # liitetään vain patient_info, ei koko user-dataa
    if logged_in_state and user_data and user_data.get("patient_info"):
        patient_info = user_data["patient_info"]
        prompt = f"{user_message}\n\nPatient info:\n{patient_info}"

    # 4) Kutsu RAG-mallia chat-historialla (lisätään myös juuri tullut user-viesti historiaan)
    history_plus_latest = history_docs + [{"sender": "user", "content": user_message}]

    try:
        raw_response = await rag_cloud.get_rag_response(prompt, history_plus_latest)
        formatted_text = utils.formatGeminiResponse(raw_response)

        # 5) Tallenna bot-vastaus
        await save_message(user_id=user_id, chat_id=chat_id, sender="bot", content=raw_response)

        return {"reply": formatted_text, "chat_id": chat_id}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Register user routes
app.include_router(user_router, prefix="/users", tags=["users"])