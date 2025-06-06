import streamlit as st
import requests

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PrivChat",
    page_icon="🤖",
    layout="wide"
)

# --- STYLING for PII Highlighting ---
# Define styles for different entity types, similar to the CSS.
entity_colors = {
    "PERSON": "#ffab91",
    "GPE": "#80cbc4",
    "LOC": "#80cbc4",
    "ORG": "#90caf9",
    "DATE": "#fff59d",
    "DEFAULT": "#f0f2f6" # A default color for other entity types
}

# This is a bit of CSS to make the colored spans look nice.
st.markdown("""
<style>
    .entity {
        padding: 0.2em 0.4em;
        margin: 0 0.2em;
        line-height: 1;
        border-radius: 0.35em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# --- HELPER FUNCTION ---
def generate_highlighted_text(original_text, entities):
    """
    Generates an HTML string with PII entities highlighted using colored spans.
    """
    # Sort entities by start character in reverse order to avoid index issues
    sorted_entities = sorted(entities, key=lambda e: e['start_char'], reverse=True)
    
    highlighted_text = original_text
    for entity in sorted_entities:
        start = entity['start_char']
        end = entity['end_char']
        label = entity['label']
        
        # Get the color for the entity type, or a default
        color = entity_colors.get(label, entity_colors["DEFAULT"])
        
        # Create the styled span
        span = (
            f'<span class="entity" style="background-color: {color}">'
            f'{highlighted_text[start:end]}'
            f'</span>'
        )
        
        # Replace the original text with the highlighted version
        highlighted_text = highlighted_text[:start] + span + highlighted_text[end:]
        
    return highlighted_text


# --- MAIN APP INTERFACE ---
st.title("PrivChat: Sanitize & Paraphrase 🤖")
st.markdown("Enter text below to detect and sanitize PII before sending it to a local LLM for paraphrasing.")

# The FastAPI backend URL
# This assumes you are running the backend locally on the default port.
FASTAPI_URL = "http://127.0.0.1:8000/api/process_prompt/"

# --- Input Form ---
with st.form("prompt_form"):
    prompt_text = st.text_area(
        "Enter your prompt here:", 
        "John Doe from Acme Inc. is visiting his colleague, Jane Smith, in Berlin next week.",
        height=150
    )
    submitted = st.form_submit_button("Sanitize & Paraphrase")

# --- Processing and Output ---
if submitted and prompt_text:
    with st.spinner("Processing... Calling backend API, running NER, and querying the LLM."):
        try:
            # Make a request to the FastAPI backend
            response = requests.post(FASTAPI_URL, json={"prompt": prompt_text})
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()

                st.subheader("Results")
                
                # Create two columns for a cleaner layout
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Highlighted PII in Prompt")
                    highlighted_html = generate_highlighted_text(data["original_prompt"], data["detected_entities"])
                    st.markdown(highlighted_html, unsafe_allow_html=True)

                with col2:
                    st.markdown("#### LLM's Paraphrased Response")
                    st.info(data["llm_response"])

                st.markdown("---")
                st.markdown("#### Detected Entities (from spaCy)")
                if data["detected_entities"]:
                    temp_data = {
                        "Entity": [ent["text"] for ent in data["detected_entities"]],
                        "Label": [ent["label"] for ent in data["detected_entities"]],
                        # "Start": [ent["start_char"] for ent in data["detected_entities"]],
                        # "End": [ent["end_char"] for ent in data["detected_entities"]],
                    }
                    st.table(temp_data)
                else:
                    st.write("No PII entities were detected.")

            else:
                # Show error from FastAPI backend
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Error from backend: {error_detail} (Status code: {response.status_code})")

        except requests.exceptions.ConnectionError:
            st.error("Connection Error: Could not connect to the FastAPI backend.")
            st.warning("Please ensure the backend server is running. Use the command: `uvicorn backend.main:app --reload`")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")