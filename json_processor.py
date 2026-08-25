import json

class JSONParseError(Exception):
    pass

def strip_code_fences(text):
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # drop opening fence (```json or ```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # drop closing fence
        text = "\n".join(lines)
    return text.strip()

def parse_gemini_json(raw_response):
    """Parse Gemini's response into a Python dict, handling common formatting issues."""
    cleaned = strip_code_fences(raw_response)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise JSONParseError(f"Gemini returned invalid JSON: {e}")
    return data


DEFAULT_SCHEMA = {
    "name": "",
    "headline": "",
    "summary": "",
    "skills": [],
    "education": [],
    "experience": [],
    "projects": [],
    "achievements": [],
    "contact": {}
}

def normalize_data(data):
    """Ensure all expected keys exist, using safe defaults for missing ones."""
    normalized = DEFAULT_SCHEMA.copy()
    for key in DEFAULT_SCHEMA:
        if key in data:
            normalized[key] = data[key]
    return normalized


def process_gemini_response(raw_response):
    data = parse_gemini_json(raw_response)
    return normalize_data(data)


if __name__ == "__main__":
    import sys
    from extractor import extract_text
    from validator import validate_and_clean
    from gemini_client import generate_content
    from prompt_builder import build_prompt

    path = sys.argv[1]
    raw_text = extract_text(path)
    cleaned = validate_and_clean(raw_text)
    prompt = build_prompt(cleaned)
    gemini_response = generate_content(prompt)

    try:
        result = process_gemini_response(gemini_response)
        print("--- PARSED DATA ---")
        for key, value in result.items():
            print(f"{key}: {value}\n")
    except JSONParseError as e:
        print(f"Error: {e}")