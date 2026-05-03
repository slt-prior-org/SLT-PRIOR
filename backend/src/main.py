import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes.professional import router as professional_router
from routes.chat import router as chat_router
from routes.auth import router as auth_router
from routes.websocket import router as websocket_router
from routes.guidelines import router as guidelines_router

app = FastAPI()


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

app.include_router(
    websocket_router,
    tags=["websocket"]
)

app.include_router(
    guidelines_router,
    prefix="/api/guidelines",
    tags=["guidelines"]
)