# PrivChat: PII Sanitization & Paraphrasing Bot

This project is a solution for the LLM Engineer coding challenge. It implements a system that identifies Personally Identifiable Information (PII) in a user's prompt, sanitizes it, and then uses a local Large Language Model (LLM) to paraphrase the text.

The project includes both the required backend logic and a fully functional frontend GUI to demonstrate a complete end-to-end system.

## Key Features

- **PII Detection**: Uses spaCy (`en_core_web_sm`) to identify named entities like names and locations.
- **Advanced Sanitization**: Replaces detected PII with indexed labels (e.g., `[PERSON_1]`, `[LOCATION_1]`) to preserve context for the LLM.
- **LLM Integration**: Connects to a local LLM via Ollama's REST API for paraphrasing.
- **Web Interface**: A simple and intuitive GUI, built with streamlit, that highlights detected PII and displays the LLM's response.
- **Configuration-Driven**: Settings like model names are managed via a `.env` file for easy modification.
- **Robust Backend**: Built with FastAPI, featuring structured logging and proper error handling.

## Project Structure
.  
├── backend/        # Contains all backend FastAPI logic  
├── .env            # Configuration file for models, etc.  
├── app.py          # streamlit frontend app  
├── README.md       # This file  
└── requirements.txt  # Python dependencies  

## Setup & Installation

**Prerequisites:**
- Python 3.9+
- [Ollama](https://ollama.com/) installed and running.
- The `llama3` model pulled (`ollama pull llama3`).

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-link>
    cd nme_llm
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download the spaCy model:**
    ```bash
    python -m spacy download en_core_web_sm
    ```

5.  **Configure the application:**
    - The project comes with a default `.env` file. You can edit `backend/.env` to change the `OLLAMA_MODEL` if needed.

## Running the Application

This project uses a separate backend (FastAPI) and frontend (Streamlit). You will need to run them in two separate terminals.

**Prerequisites:** Make sure you have completed the full setup and installation as described above. Ensure Ollama is running.

### Step 1: Run the Backend Server

Open your first terminal, navigate to the project root, and run the FastAPI application using uvicorn:

```bash
# This starts the API server on [http://127.0.0.1:8000](http://127.0.0.1:8000)
uvicorn backend.main:app --reload
```

### Step 2: Run the Frontend

Run the following command in the terminal which will automatically redirect you to the webpage

```bash
streamlit run app.py
```
