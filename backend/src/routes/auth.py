import logging
import os
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from ai_model import rag_cloud

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

from database.db import users_collection
from database.models import AuthResponse, StatusWithUserResponse, UserModel, LoginRequest

router = APIRouter()
logging.basicConfig(level=logging.INFO)

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="ID",
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=8,
)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def _public_user(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "email": doc.get("email"),
        "role": doc.get("role"),
        "patient_info": doc.get("patient_info"),
    }

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id or not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    user["_id"] = str(user["_id"])
    return user


@router.post("/register", response_model=AuthResponse)
async def register_user(user: UserModel, request: Request):

    user_dict = user.model_dump() 

    #Check uniqueness of email
    existing_user = await users_collection.find_one({"email": user_dict["email"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Hashing password
    user_dict["password"] = pwd_context.hash(user_dict["password"])

    result = await users_collection.insert_one(user_dict)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to insert user.")
    
    user_id = str(result.inserted_id) 

    created = await users_collection.find_one({"_id": result.inserted_id})
    token = create_access_token(user_id)

    logging.info(f"User registered: {user_id}")
    return {"token": token, "user": _public_user(created)}       

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request):

    user = await users_collection.find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    hashed = user.get("password")
    if not hashed or not pwd_context.verify(body.password, hashed):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]))
    return {"token": token, "user": _public_user(user)}

@router.get("/me")
async def me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return the current user based on the Bearer token."""
    return {"user": _public_user(current_user)}

@router.put("/me")
async def update_me(
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update current user's profile fields.

    Notes:
      - We intentionally block updating password/email here.
      - Extend allowed fields as needed.
    """
    blocked = {"password", "email", "_id", "id"}
    for k in list(updates.keys()):
        if k in blocked:
            updates.pop(k, None)

    if not updates:
        return {"user": _public_user(current_user)}

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": updates},
    )
    refreshed = await users_collection.find_one({"_id": current_user["_id"]})
    return {"user": _public_user(refreshed)}

@router.post("/logout")
async def logout():
    """JWT is stateless; 'logout' is handled on the client by deleting the token."""
    return {"status": "success"}