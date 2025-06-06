# backend/main.py

import spacy
import ollama
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import settings
from .sanitizer import sanitize_prompt_advanced

# --- 1. INITIALIZATION & CONFIGURATION ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="An API to detect PII, sanitize the prompt, and get a response from a local LLM."
)

try:
    nlp = spacy.load(settings.SPACY_MODEL)
    logging.info(f"Successfully loaded spaCy model: {settings.SPACY_MODEL}")
except OSError:
    logging.error(f"Spacy model '{settings.SPACY_MODEL}' not found.")
    logging.error(f"Please run 'python -m spacy download {settings.SPACY_MODEL}' to install it.")
    exit()

class PromptRequest(BaseModel):
    prompt: str

# --- 2. API ENDPOINTS ---

@app.get("/")
async def read_root():
    """
    Serve the main HTML file for the user interface.
    """


@app.post("/api/process_prompt/")
def process_prompt(request: PromptRequest):
    """
    This endpoint performs the core functionality:
    1. Receives a prompt.
    2. Uses spaCy to detect named entities (PII).
    3. Uses the advanced sanitizer to create a sanitized prompt.
    4. Sends the sanitized prompt to a local LLM via Ollama.
    5. Returns the detected entities (with character offsets) and the LLM response.
    """
    user_prompt = request.prompt
    logging.info(f"Received prompt: '{user_prompt}'")

    # --- 3. NAMED ENTITY RECOGNITION (NER) ---
    doc = nlp(user_prompt)
    entities = [
        {"text": ent.text, "label": ent.label_, "start_char": ent.start_char, "end_char": ent.end_char}
        for ent in doc.ents
    ]
    logging.info(f"Detected entities: {entities}")

    # --- 4. ADVANCED PROMPT SANITIZATION ---
    sanitized_prompt = sanitize_prompt_advanced(doc)
    logging.info(f"Sanitized prompt for LLM: '{sanitized_prompt}'")

    # --- 5. LOCAL LLM INFERENCE ---
    try:
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {'role': 'user', 'content': f"Politely and concisely paraphrase this: {sanitized_prompt}"}
            ]
        )
        llm_response = response['message']['content']
        logging.info(f"Received response from LLM: '{llm_response}'")
    except Exception as e:
        logging.error(f"Error contacting Ollama: {e}")
        raise HTTPException(status_code=503, detail="Could not get response from Ollama. Is the service running?")

    # --- 6. RETURN RESPONSE ---
    return {
        "original_prompt": user_prompt,
        "detected_entities": entities,
        "llm_response": llm_response,
    }