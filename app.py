import streamlit as st
import requests

st.set_page_config(
    page_title="PrivChat",
    layout="wide"
)

entity_colors = {
    "PERSON": "#ffab91",
    "GPE": "#80cbc4",
    "LOC": "#80cbc4",
    "ORG": "#90caf9",
    "DATE": "#fff59d",
    "DEFAULT": "#f0f2f6" 
}

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


def generate_highlighted_text(original_text, entities):
    sorted_entities = sorted(entities, key=lambda e: e['start_char'], reverse=True)
    
    highlighted_text = original_text
    for entity in sorted_entities:
        start = entity['start_char']
        end = entity['end_char']
        label = entity['label']
        
        color = entity_colors.get(label, entity_colors["DEFAULT"])
        
        span = (
            f'<span class="entity" style="background-color: {color}">'
            f'{highlighted_text[start:end]}'
            f'</span>'
        )
        
        highlighted_text = highlighted_text[:start] + span + highlighted_text[end:]
        
    return highlighted_text


st.title("PrivChatBot")
st.markdown("Enter text below to detect and sanitize PII before sending it to a local LLM for paraphrasing.")

# FAST API part

FASTAPI_URL = "http://127.0.0.1:8000/api/process_prompt"

with st.form("prompt_form"):
    prompt_text = st.text_area(
        "Enter your prompt here:", 
        "John Doe from Acme Inc. is visiting his colleague, Jane Smith, in Berlin next week.",
        height=150
    )
    submitted = st.form_submit_button("Send Prompt")

if submitted and prompt_text:
    with st.spinner("Processing... Calling backend API, running NER, and querying the LLM."):
        try:
            response = requests.post(FASTAPI_URL, json={"prompt": prompt_text})
            
            if response.status_code == 200:
                data = response.json()
                print(data)  # Debugging line to check the response structure
                st.subheader("Results")
                
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Detected PII in Prompt")
                    highlighted_html = generate_highlighted_text(data["original_prompt"], data["detected_entities"])
                    st.markdown(highlighted_html, unsafe_allow_html=True)

                with col2:
                    st.markdown("#### Sanitized Prompt")
                    st.info(data["sanitized_prompt"])

                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Output from LLM of sanitized prompt")
                    st.info(data["llm_response"])

                with col2:
                    st.markdown("#### Final output after adding entities")
                    st.info(data["sanitized_response"])
            
                st.markdown("---")
                st.markdown("#### Detected Entities (from spaCy)")
                if data["detected_entities"]:
                    temp_data = {
                        "Entity": [ent["text"] for ent in data["detected_entities"]],
                        "Label": [ent["label"] for ent in data["detected_entities"]],
                    }
                    st.table(temp_data)
                else:
                    st.write("No PII entities were detected.")

            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Error from backend: {error_detail} (Status code: {response.status_code})")

        except requests.exceptions.ConnectionError:
            st.error("Connection Error: Could not connect to the FastAPI backend.")
            st.warning("Please ensure the backend server is running. Use the command: `uvicorn backend.main:app --reload`")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")