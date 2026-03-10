import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Haetaan kirjautuneen käyttäjän tiedot ja kirjautumisen tila
from routes.users import router as user_router, current_user_id, logged_in
from routes.professional import router as professional_router
from routes.chat import router as chat_router
from routes.auth import router as auth_router

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

# Register user routes
app.include_router(
    user_router,
    prefix="/api/users",
    tags=["users"]
    )

app.include_router(
    professional_router,
    prefix="/api/professional",
    tags=["professional"]
)

app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["chat"]
)

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"]
)
