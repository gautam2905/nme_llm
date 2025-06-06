# backend/config.py

import os
from pydantic_settings import BaseSettings

# Load the .env file from the parent directory of the 'backend' folder
# This makes the settings accessible regardless of where the script is run from
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

# Create a single settings instance to be imported by other modules
settings = Settings()