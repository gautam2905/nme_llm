import spacy
import ollama
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
# from requests import json
import requests
import json

from .config import settings
from collections import defaultdict

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # logger initialize

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="An API to detect PII, sanitize the prompt, and get a secure prompt from local llm."
)

url = "http://localhost:11434/api/generate"
headers = {
    "Content-Type": "application/json",
}


try:
    nlp = spacy.load(settings.SPACY_MODEL)
    logging.info(f"Successfully loaded spaCy model: {settings.SPACY_MODEL}")
except OSError:
    logging.error(f"Spacy model '{settings.SPACY_MODEL}' not found.")
    logging.error(f"Please run 'python -m spacy download {settings.SPACY_MODEL}' to install it.")
    exit()

class PromptRequest(BaseModel):
    prompt: str


def sanitize_prompt_advanced(doc):
    sanitized_prompt = doc.text
    entity_counts = defaultdict(int)
    replacements = []

    for ent in doc.ents:
        entity_counts[ent.label_] += 1
        indexed_label = f"[{ent.label_}_{entity_counts[ent.label_]}]"
        replacements.append((ent.start_char, ent.end_char, indexed_label))

    for start, end, label in sorted(replacements, key=lambda x: x[0], reverse=True):
        sanitized_prompt = sanitized_prompt[:start] + label + sanitized_prompt[end:]

    return sanitized_prompt


@app.post("/api/process_prompt/")
def process_prompt(request: PromptRequest):
    user_prompt = request.prompt
    logging.info(f"Received prompt: '{user_prompt}'")

    doc = nlp(user_prompt)
    entities = [
        {"text": ent.text, "label": ent.label_, "start_char": ent.start_char, "end_char": ent.end_char}
        for ent in doc.ents
    ]
    logging.info(f"Detected entities: {entities}")

    sanitized_prompt = sanitize_prompt_advanced(doc)
    logging.info(f"Sanitized prompt for LLM: '{sanitized_prompt}'")

    try:
        response = requests.post(
            url,
            headers=headers,
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": sanitized_prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            # reponse_text = response.text
            data = response.json()
            logging.info(f"Received response from Ollama: '{data}'")
            llm_response = data["response"]
        else:
            logging.error(f"Error contacting Ollama: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error contacting Ollama")

        # response = ollama.chat(
        #     model=settings.OLLAMA_MODEL,
        #     messages=[
        #         {'role': 'user', 'content': f"{sanitized_prompt}"}
        #     ]
        # )
        # llm_response = response['message']['content']
        logging.info(f"Received response from LLM: '{llm_response}'")
    except Exception as e:
        logging.error(f"Error contacting Ollama: {e}")
        raise HTTPException(status_code=503, detail="Could not get response from Ollama. Is the service running?")

    return {
        "original_prompt": user_prompt,
        "detected_entities": entities,
        "llm_response": llm_response,
    }