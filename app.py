# app.py
import sys

from extractor import extract_text, ExtractionError
from validator import validate_and_clean, check_file_exists, ValidationError
from gemini_client import generate_content, GeminiConfigError, GeminiAPIError
from prompt_builder import build_prompt
from json_processor import process_gemini_response, JSONParseError
from generator import choose_template, render_portfolio


def main():
    if len(sys.argv) < 2:
        print("Usage: python app.py <path_to_resume.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Test 1 — missing resume
    try:
        check_file_exists(pdf_path)
    except ValidationError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Extraction (handles Test 8 — corrupted/unreadable PDF too)
    try:
        raw_text = extract_text(pdf_path)
    except ExtractionError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test 2 — empty/short resume
    try:
        cleaned_text = validate_and_clean(raw_text)
    except ValidationError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test 5 — missing API key / Test 6 — API failure
    prompt = build_prompt(cleaned_text)
    try:
        gemini_response = generate_content(prompt)
    except GeminiConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except GeminiAPIError as e:
        print(f"API error: {e}")
        sys.exit(1)

    # Test 7 — invalid JSON
    try:
        data = process_gemini_response(gemini_response)
    except JSONParseError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test 3 — valid resume / Test 4 — missing sections (handled by template's conditional blocks)
    template_folder = choose_template()
    output_path = render_portfolio(data, template_folder)

    print(f"\n✅ Portfolio generated successfully: {output_path}")
    print("Open it in your browser to view.")


if __name__ == "__main__":
    main()