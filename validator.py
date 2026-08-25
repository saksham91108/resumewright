class ValidationError(Exception):
    """Raised when the resume fails a validation check."""
    pass

MIN_LENGTH = 50  # tweak based on testing — same idea as extractor's threshold

def validate_text(text):
    """Check that extracted text is usable. Raises ValidationError if not."""
    if text is None:
        raise ValidationError("No text was extracted from the resume.")

    stripped = text.strip()

    if len(stripped) == 0:
        raise ValidationError("The resume appears to be empty.")

    if len(stripped) < MIN_LENGTH:
        raise ValidationError(
            f"The resume text is too short ({len(stripped)} characters) to process."
        )

    return True

#code cleaning
import re

def clean_text(text):
    """Remove excess whitespace and blank lines from resume text."""
    # Collapse multiple spaces/tabs into one
    text = re.sub(r'[ \t]+', ' ', text)

    # Strip trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]

    # Remove empty lines (but keep single blank lines between sections if you want spacing —
    # here we drop them entirely for a compact clean version)
    lines = [line for line in lines if line]

    return '\n'.join(lines)

#Combine into one entry point
def validate_and_clean(text):
    """Validate raw extracted text, then return cleaned text."""
    validate_text(text)
    return clean_text(text)


#Handle the missing-file case
import os

def check_file_exists(pdf_path):
    if not os.path.exists(pdf_path):
        raise ValidationError(f"Resume file not found: {pdf_path}")

#Test it standalone
if __name__ == "__main__":
    import sys
    from extractor import extract_text, ExtractionError

    path = sys.argv[1]

    try:
        raw = extract_text(path)
    except ExtractionError as e:
        print(f"Extraction failed: {e}")
        sys.exit(1)

    try:
        cleaned = validate_and_clean(raw)
        print("--- CLEANED TEXT ---")
        print(cleaned)
        print(f"\n--- LENGTH: {len(cleaned)} chars ---")
    except ValidationError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)