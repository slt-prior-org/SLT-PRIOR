import logging
from ai_model import rag_cloud
from fastapi import APIRouter, HTTPException, FastAPI
from database.db import users_collection
from database.models import UserModel, RegisterModel
from bson import ObjectId
from flask import jsonify
from fastapi import Request
from passlib.context import CryptContext

app = FastAPI()
router = APIRouter()
logging.basicConfig(level=logging.INFO)

# Global variables for user session
logged_in = False
current_user_id = None
current_user_data = None


@router.post("/login")
async def check_user_id(user_data: dict, request: Request):  # Lisätty Request-parametri
    """
    Kirjautuu sisään käyttäjänä, joka on jo olemassa MongoDB:ssä.
    Tarkistaa onko käyttäjä olemassa ja palauttaa käyttäjätiedot.
    Jos käyttäjää ei löydy, palauttaa virheilmoituksen.
    """
    
    # Set global variables
    global logged_in, current_user_id, current_user_data

    try:
        user_id = user_data.get("user_id")
        
        if not ObjectId.is_valid(user_id):
            return {"status": "error", "message": "invalid_id"}

        # tekee saman työn kuin main.py:ssä
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return {"status": "error", "message": "not_found"}

        user["_id"] = str(user["_id"])
        
        # Päivitä  globaalit muuttujat JA sovelluksen tila
        logged_in = True
        current_user_id = user["_id"]
        current_user_data = user
        request.app.state.logged_in = True  # <-- Tallenna sovelluksen tilaan eli mainiin
        request.app.state.current_user_id = user["_id"]
        request.app.state.current_user_data = user

        logging.info(f"User logged in: {user_id}")
        return {"status": "success", "user": user, "message": "success"}

    except Exception as e:
        logging.exception("Login error")
        return {"status": "error", "message": "server_error"}


@router.post("/logout")
async def logout(request: Request):
    """
    Kirjaa käyttäjän ulos ja nollaa globaalit muuttujat.
    """
    global logged_in, current_user_id, current_user_data
    logged_in = False
    current_user_id = None
    current_user_data = None

    request.app.state.logged_in = False
    request.app.state.current_user_id = None
    request.app.state.current_user_data = None

    rag_cloud.memory.chat_memory.clear()  # Tyhjennetään muisti

    logging.info("User logged out successfully.")
    return {"status": "success", "message": "logout_success"}

# Create new user to MongoDB, returns unique dataId
@router.post("/", response_model=dict)
async def create_user(user: UserModel, request: Request):
    try:
        user_dict = user.model_dump() 

        result = await users_collection.insert_one(user_dict)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to insert user.")

        # Convert ObjectId to string
        object_id = str(result.inserted_id)

        logged_in = False
        current_user_id = None

        request.app.state.logged_in = True
        request.app.state.current_user_id = str(result.inserted_id)

        logging.info(f"✅ User saved with ObjectId: {object_id}")
        return {"user_id": object_id, "message": "User created successfully"}
    
    except Exception as e:
        logging.exception("❌ Unexpected error occurred while creating user")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again later.")

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    # Force Argon2id (important)
    argon2__type="ID",
    # Sensible starting parameters (tune as needed)
    argon2__time_cost=2,
    argon2__memory_cost=102400,   # KiB (≈ 100 MB)
    argon2__parallelism=8,
)


@router.post("/register", response_model=dict)
async def register_user(user: RegisterModel, request: Request):

    user_dict = user.model_dump() 

    # Hashing password
    plaintextPw = user_dict["password"]
    hashedPw = pwd_context.hash(plaintextPw)
    user_dict["password"] = hashedPw

    result = await users_collection.insert_one(user_dict)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to insert user.")
    
    object_id = str(result.inserted_id) 

    logged_in = False
    current_user_id = None

    request.app.state.logged_in = True
    request.app.state.current_user_id = str(result.inserted_id)

    logging.info(f"✅ User saved with ObjectId: {object_id}")
    return {"user_id": object_id, "message": "User created successfully"}       

# Get user by userId
""""
@router.get("/{user_id}", response_model=UserModel)
async def get_user(user_id: str):
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
"""


# Modify user data
""""
@router.put("/{user_id}", response_model=UserModel)
async def update_user(user_id: str, user: UserModel):
    existing_user = await users_collection.find_one({"user_id": user_id})

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    await users_collection.update_one({"user_id": user_id}, {"$set": user.model_dump()})
    return user
"""

# Delete user by userId
""""
@router.delete("/{user_id}")
async def delete_user(user_id: str):
    delete_result = await users_collection.delete_one({"user_id": user_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
"""

@router.get("/id/{user_id}")
async def get_user_by_object_id(user_id: str):
    """
    Hakee user-dokumentin MongoDB:stä _id-kentän perusteella.
    Palauttaa kaiken dokumentista JSON-muodossa.
    """
    try:
        # Tarkistetaan onko user_id validi ObjectId
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id format.")

        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user["_id"] = str(user["_id"])
        return user

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# User tietojen näyttäminen endpoint
@router.get("/current-user")
async def get_current_user(request: Request):
    """Palauttaa kirjautuneen käyttäjän tiedot"""
    if not request.app.state.logged_in:
        return {"status": "error", "message": "not_logged_in"}
    
    if not request.app.state.current_user_data:
        return {"status": "error", "message": "no_user_data"}
    
    return {
        "status": "success",
        "user": request.app.state.current_user_data
    }
# Kirjautumistilan tarkistus tietojen tuomista varten
@router.get("/check-session")
async def check_session(request: Request):
    """Tarkistaa kirjautumistilan"""
    return {
        "isLoggedIn": request.app.state.logged_in,
        "userId": request.app.state.current_user_id
    }
# endpoint tietojen tallentamista varten
@router.put("/id/{user_id}")
async def update_user(user_id: str, user_data: dict, request: Request):
    try:
        if not ObjectId.is_valid(user_id):
            return {"status": "error", "message": "invalid_id"}

        # Kenttien validointi
        if not all(key in user_data for key in ["weight", "height"]):
            return {"status": "error", "message": "missing_required_fields"}

        # Numeerien konvertointi
        try:
            user_data["weight"] = float(user_data["weight"])
            user_data["height"] = float(user_data["height"])
        except (ValueError, TypeError):
            return {"status": "error", "message": "invalid_numeric_values"}

        # tarkistetaan käyttäjän olemassaolo
        existing_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            return {"status": "error", "message": "user_not_found"}

        # tietokannan päivitys
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": user_data}
        )

        if result.modified_count == 0:
            return {"status": "error", "message": "no_changes"}

        # haetaan päivitetty käyttäjä
        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])

        # päivitetään sessio
        request.app.state.current_user_data = updated_user

        return {"status": "success", "user": updated_user}

    except Exception as e:
        logging.error(f"Update failed: {str(e)}")
        return {"status": "error", "message": "update_failed"}