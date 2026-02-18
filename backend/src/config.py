import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GEMINI_API")
    BUCKET_NAME: str = "training_data-1"
    PERSIST_DIRECTORY: str = "/app/chroma"

settings = Settings()
