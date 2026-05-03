import logging
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from config import settings

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

from database.db import users_collection
from database.models import AuthResponse, PatientInfo, UserModel, LoginRequest, UserDetailResponse

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/swagger_login")

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRES_MIN)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def _public_user(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "email": doc.get("email"),
        "role": doc.get("role"),
        "patient_info": doc.get("patient_info"),
    }

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
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
        raise HTTPException(status_code=401, detail="loginStatus.invalid_credentials")

    hashed = user.get("password")
    if not hashed or not pwd_context.verify(body.password, hashed):
        raise HTTPException(status_code=401, detail="loginStatus.invalid_credentials")

    token = create_access_token(str(user["_id"]))
    return {"token": token, "user": _public_user(user)}

# This endpoint is needed only to enable Swagger UI OAuth2 login.
# It returns a JWT in the correct format so Swagger can automatically
# add it to the Authorization header (Bearer <token>) for subsequent requests.

@router.post("/swagger_login")
async def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Swagger login (OAuth2PasswordBearer)
    - username = user's email
    - password = user's password
    """
    email = form_data.username
    password = form_data.password

    user = await users_collection.find_one({"email": email})
    if not user or not pwd_context.verify(password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]))
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserDetailResponse)
async def me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Return the current user based on the Bearer token."""
    return _public_user(current_user)

@router.put("/me", response_model=UserDetailResponse)
async def update_me(
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    blocked = {"password", "email", "_id", "id"}
    for k in list(updates.keys()):
        if k in blocked:
            updates.pop(k, None)

    if "patient_info" in updates and isinstance(updates["patient_info"], dict):
        existing_patient_info = current_user.get("patient_info", {}) or {}
        merged_patient_info = {**existing_patient_info, **updates["patient_info"]}

        # remove empty values so partial updates don't create invalid shapes
        merged_patient_info = {
            k: v for k, v in merged_patient_info.items()
            if v is not None
        }

        updates["patient_info"] = PatientInfo(**merged_patient_info).model_dump()

    if not updates:
        return _public_user(current_user)

    await users_collection.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": updates},
    )

    refreshed = await users_collection.find_one({"_id": ObjectId(current_user["_id"])})
    return _public_user(refreshed)

@router.post("/logout")
async def logout():
    """JWT is stateless; 'logout' is handled on the client by deleting the token."""
    return {"status": "success"}