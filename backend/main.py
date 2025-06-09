import spacy
import ollama
import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import json

from .config import settings
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # logger initialize

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="An API to detect PII, sanitize the prompt, and get a secure prompt from local llm."
)

headers = {
    "Content-Type": "application/json"
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
    placeholder_map = {}

    for ent in doc.ents:
        entity_counts[ent.label_] += 1
        indexed_label = f"[{ent.label_}_{entity_counts[ent.label_]}]"
        replacements.append((ent.start_char, ent.end_char, indexed_label))
        placeholder_map[indexed_label] = ent.text


    for start, end, label in sorted(replacements, key=lambda x: x[0], reverse=True):
        sanitized_prompt = sanitized_prompt[:start] + label + sanitized_prompt[end:]

    return sanitized_prompt, placeholder_map


@app.post("/api/process_prompt")
def process_prompt(request: PromptRequest):
    user_prompt = request.prompt
    logging.info(f"Received prompt: '{user_prompt}'")

    # Spacy NLP processing
    doc = nlp(user_prompt)
    entities = [
        {"text": ent.text, "label": ent.label_, "start_char": ent.start_char, "end_char": ent.end_char}
        for ent in doc.ents
    ]
    logging.info(f"Detected entities: {entities}")

    sanitized_prompt, placeholder = sanitize_prompt_advanced(doc)
    logging.info(f"Sanitized prompt for LLM: '{sanitized_prompt}'")


    # REST API call to Ollama

    try:
        payload = {
            "model": "llama3",
            "prompt": sanitized_prompt,
            "stream": False
        }
        response = requests.post(settings.REST_API_URL, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            data = response.json()
            logging.info(f"Received response from Ollama: '{data}'")
            llm_response = data["response"]
        else:
            logging.error(f"Error contacting Ollama: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error contacting Ollama")

        logging.info(f"Received response from LLM: '{llm_response}'")

    except Exception as e:
        logging.error(f"Error contacting Ollama: {e}")
        raise HTTPException(status_code=503, detail="Could not get response from Ollama. Is the service running?")

    sanitized_response = llm_response 
    for label, text in placeholder.items():
        sanitized_response = sanitized_response.replace(label, text)
        logging.info(f"Replaced placeholder '{label}' with original text '{text}' in LLM response.")

    print(f"Sanitized response: {sanitized_response}")

    return {
        "original_prompt": user_prompt,
        "detected_entities": entities,
        "llm_response": llm_response,
        "sanitized_prompt": sanitized_prompt,
        "sanitized_response": sanitized_response,
    }