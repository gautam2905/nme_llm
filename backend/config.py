# backend/config.py

import os
from pydantic_settings import BaseSettings

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

class Settings(BaseSettings):
    """
    Pydantic settings model to manage application configuration from environment variables.
    """
    SPACY_MODEL: str = "en_core_web_sm"
    OLLAMA_MODEL: str = "llama3"
    API_TITLE: str = "PrivChat API"
    API_VERSION: str = "1.1.0"

    class Config:
        env_file = env_path
        env_file_encoding = 'utf-8'

settings = Settings()