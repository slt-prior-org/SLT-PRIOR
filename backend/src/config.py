import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # External services
    GOOGLE_API_KEY: str = os.getenv("GEMINI_API") or os.getenv("GOOGLE_API_KEY")
    BUCKET_NAME: str = "training_data-1"
    PERSIST_DIRECTORY: str = "/app/chroma"

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))


settings = Settings()

if not settings.JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in environment variables")
