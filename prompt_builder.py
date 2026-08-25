RESUME_JSON_SCHEMA = """
{
  "name": "string",
  "headline": "string",
  "summary": "string",
  "skills": ["string"],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "years": "string"
    }
  ],
  "experience": [
    {
      "title": "string",
      "company": "string",
      "duration": "string",
      "description": "string"
    }
  ],
  "projects": [
    {
      "title": "string",
      "description": "string",
      "technologies": ["string"]
    }
  ],
  "achievements": ["string"],
  "contact": {
    "email": "string",
    "phone": "string",
    "linkedin": "string",
    "github": "string"
  }
}
"""


def build_prompt(cleaned_resume_text):
    return f"""You are a strict resume-to-JSON converter. Follow these rules exactly.

RULES:
1. Use ONLY information explicitly present in the resume text below.
2. Do NOT invent, infer, guess, or add any skills, experience, projects, achievements, companies, dates, or links that are not explicitly stated in the resume.
3. If a section has no information in the resume, use an empty string "" or empty array [] for that field. Do NOT write placeholder text like "Not specified" or "N/A".
4. Return ONLY valid JSON. No markdown code fences, no explanations, no preamble, no text before or after the JSON.
5. Follow this exact schema:

{RESUME_JSON_SCHEMA}

RESUME TEXT:
{cleaned_resume_text}

Return the JSON now:"""



if __name__ == "__main__":
    import sys
    from extractor import extract_text
    from validator import validate_and_clean
    from gemini_client import generate_content

    path = sys.argv[1]
    raw = extract_text(path)
    cleaned = validate_and_clean(raw)
    prompt = build_prompt(cleaned)

    print("--- PROMPT PREVIEW (first 500 chars) ---")
    print(prompt[:500])
    print("...\n")

    print("--- GEMINI RAW RESPONSE ---")
    response = generate_content(prompt)
    print(response)