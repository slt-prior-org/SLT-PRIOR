from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Haetaan kirjautuneen käyttäjän tiedot ja kirjautumisen tila
from routes.users import router as user_router, current_user_id, logged_in
from ai_model import rag_cloud
from ai_model import utils
from ai_model.classifier import classify_question, Classification
from ai_model.emergency import detect_emergency
from bson import ObjectId
from database.db import users_collection


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
    1) Lukee frontendiltä tulevan 'message' ja (optionaalisen) 'user_id' -kentän.
    2) Jos user_id on annettu ja kelvollinen, hakee käyttäjädatan MongoDB:stä.
    3) Yhdistää käyttäjädatan promtiin ja kutsuu RAG-mallia.
    """
    
    logged_in = app.state.logged_in 

    # Muutettu käyttämään payloadia, requestin sijaan
    user_message = payload.get("message")
    user_id = app.state.current_user_id

    # jos haluaa muuttaa niin voi hakea user_datan suoraan globaalista muuttujasta ja käyttää sitä
    # nyt data haetaan ensin MongoDB:stä ja sitten asetetaan globaaliksi muuttujaksi
    # ja uudelleen sama tässä mainissa

    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required.")

    # 1) Haetaan käyttäjädata, jos user_id on annettu
    user_data = None
    if user_id:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format.")
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])  # Muunnetaan _id stringiksi
            user_data = user_doc

    # 2) Hätätilanteen tunnistus ENNEN luokittelua ja RAG-kutsua
    emergency = detect_emergency(user_message)
    if emergency:
        return {
            "reply": emergency.emergency_message_en,
            "classification": "EMERGENCY",
            "is_emergency": True
        }

    # 3) Luokitellaan kysymys ENNEN RAG-kutsua (EU AI Act)
    classification_result = await classify_question(
        question=user_message,
        user_data=user_data,
        is_logged_in=logged_in
    )

    # 4) Rakennetaan prompt, jossa lisätään käyttäjädata mukaan
    if logged_in:
        if user_data:
            prompt = f"{user_message}\n\nUser data:\n{user_data}"
        else:
            prompt = user_message
    else:
        prompt = user_message

    # 5) Kutsutaan RAG-mallia
    try:
        raw_response = await rag_cloud.get_rag_response(prompt)
        formatted_text = utils.formatGeminiResponse(raw_response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    # 6) Palautetaan vastaus luokittelun perusteella
    if classification_result.classification == Classification.SAFE:
        return {
            "reply": formatted_text,
            "classification": "SAFE"
        }
    else:
        # NEEDS_REVIEW: käyttäjälle turvallinen viesti, luonnos ammattilaiselle
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
            "classification": "NEEDS_REVIEW",
            "requires_professional": True,
            "draft_response": formatted_text,
            "classification_reasoning": classification_result.reasoning
        }

# Register user routes
app.include_router(user_router, prefix="/users", tags=["users"])
