# backend/sanitizer.py

from collections import defaultdict

def sanitize_prompt_advanced(doc):
    """
    Replaces named entities in a spaCy Doc object with indexed labels.
    e.g., "John Doe and Jane Doe went to Paris." ->
          "[PERSON_1] and [PERSON_2] went to [GPE_1]."

    Args:
        doc (spacy.Doc): The processed document from spaCy.

    Returns:
        str: The sanitized prompt string.
    """
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