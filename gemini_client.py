import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

class GeminiConfigError(Exception):
    pass

class GeminiAPIError(Exception):
    pass

def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiConfigError("GEMINI_API_KEY not found. Check your .env file.")
    return genai.Client(api_key=api_key)

def generate_content(prompt, model="gemini-3.5-flash"):
    """Send a prompt to Gemini and return the raw text response."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        raise GeminiAPIError(f"Gemini API call failed: {e}")

if __name__ == "__main__":
    try:
        result = generate_content("Say hello in one sentence.")
        print("--- GEMINI RESPONSE ---")
        print(result)
    except (GeminiConfigError, GeminiAPIError) as e:
        print(f"Error: {e}")