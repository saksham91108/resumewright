# resumewright

AI-assisted resume → portfolio generator. Upload a resume (PDF, DOCX, or TXT), and Gemini extracts structured content that gets rendered into a styled, static portfolio website — no invented information, no manual copy-pasting.

Live pipeline: `resume file → extract → validate → Gemini → JSON → render → portfolio.html`

Two ways to use it:
- **CLI** (`app.py`) — generate a portfolio from the terminal
- **Web app** (`web/`) — FastAPI-powered upload UI with a live template picker, deployable to Vercel

## How it works

```
resume.pdf / .docx / .txt
    ↓  extractor.py       (pdfplumber + OCR fallback for PDFs, python-docx for DOCX, plain read for TXT)
raw text
    ↓  validator.py        (checks empty/too short, cleans whitespace)
cleaned text
    ↓  prompt_builder.py   (controlled, no-hallucination prompt + JSON schema)
    ↓  gemini_client.py    (sends to Gemini)
raw JSON response
    ↓  json_processor.py   (strips code fences, parses, normalizes shape)
structured data (dict)
    ↓  generator.py        (renders via Jinja2 into one of 4 templates)
portfolio.html + style.css
```

## Project structure

```
resumewright/
├── app.py                  # CLI entry point
├── extractor.py             # PDF/DOCX/TXT text extraction
├── validator.py             # validation & cleaning
├── gemini_client.py         # Gemini API integration
├── prompt_builder.py        # controlled prompt + JSON schema
├── json_processor.py        # parses/validates Gemini's JSON response
├── generator.py              # renders HTML via Jinja2, template picker (CLI)
├── templates/                # 4 portfolio templates (template1–template4)
├── sample_resumes/           # test files
├── output/                   # CLI-generated portfolio.html + style.css
├── web/                      # FastAPI web app
│   ├── main.py                # routes: /, /generate, /view, /download
│   ├── templates/             # index.html (upload), result.html
│   ├── static/                # style.css, script.js
│   ├── requirements.txt
│   └── vercel.json
├── .env.example
├── requirements.txt
├── ai_usage_log.md
└── README.md
```

## Setup (local)

**1. Clone and create a virtual environment**
```bash
git clone https://github.com/saksham91108/resumewright.git
cd resumewright
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
pip install -r web/requirements.txt   # only needed if running the web app
```

**2. Install system dependencies (required for scanned-PDF OCR fallback only)**

Not needed for DOCX/TXT, or for PDFs with real embedded text — only for scanned/image-based PDFs.
- **Tesseract OCR:** https://github.com/UB-Mannheim/tesseract/wiki
- **Poppler:** https://github.com/oschwartz10612/poppler-windows/releases

Add both to your system PATH, then verify:
```bash
tesseract --version
pdftoppm -v
```

**3. Get your own Gemini API key**

Generate one at https://aistudio.google.com/apikey. **Do not use anyone else's key, and never commit yours.**

Create your own `.env` file in the project root (copy `.env.example`):
```
GEMINI_API_KEY=your_own_key_here
```

`.env` is gitignored — every contributor needs their own local copy with their own key.

## Running it

**CLI:**
```bash
python app.py sample_resumes/sample.pdf
```
Prompts you to pick a template (1–4), then writes `output/portfolio.html` + `output/style.css`.

**Web app:**
```bash
cd web
uvicorn main:app --reload
```
Open `http://127.0.0.1:8000`.

## Supported input formats

`.pdf` (direct text extraction, OCR fallback for scanned PDFs), `.docx` (paragraphs + table cells), `.txt` (plain text, multi-encoding fallback).

## Deploying the web app (Vercel)

1. `vercel.json` must sit at the repo root pointing into `web/` (already configured)
2. In the Vercel dashboard → Project Settings → Environment Variables, set `GEMINI_API_KEY` — Vercel does **not** read your local `.env`
3. **Known limitation:** Vercel's serverless functions can't run Tesseract, so scanned/image-based PDFs won't OCR-fallback in production. Direct-text PDFs, DOCX, and TXT all work fine. This works normally when run locally.
4. Generated output is written to `/tmp` on Vercel, which is ephemeral — fine for "generate → view/download immediately," not for permanent hosting of past results.

## Prompt design

The Gemini prompt (`prompt_builder.py`) enforces: use only resume-stated information (no invented skills/dates/companies), return empty values for missing sections instead of placeholder text, and return valid JSON only. `json_processor.py` defensively strips markdown code fences and safely parses the response regardless.

## Model choice

Uses the `gemini-flash-latest` alias rather than a pinned version — pinned model names were retired by Google multiple times during development, breaking the app each time. The alias tracks whatever Google currently recommends.

## Limitations

- OCR accuracy on scanned/image PDFs depends on Tesseract and can struggle with unusual fonts or multi-column layouts
- No automated fact-checking pass beyond prompt constraints — Gemini's output is treated as a draft and relies on the prompt's anti-hallucination rules
- English-language resumes assumed
- OCR fallback unavailable in the Vercel deployment (see above)

## Testing

All required test cases pass: missing file, empty/too-short resume, valid resume, missing sections (hidden, not fabricated), missing API key, invalid API key, malformed JSON from Gemini, and corrupted/unreadable file — each fails with a clean, specific error rather than a crash.

## Contributors

- [@saksham91108](https://github.com/saksham91108) — project owner
- Contributor 2
- Contributor 3
- Contributor 4
- Contributor 5

Each contributor works with their **own local `.env`** containing their **own Gemini API key** — keys are never shared or committed. See "Setup (local)" above.

## Working as a team — quick reference

**Project owner** pushes the initial repo (see setup commands below). **Everyone else** clones and works on feature branches:

```bash
git clone https://github.com/saksham91108/resumewright.git
cd resumewright
git checkout -b your-feature-branch
# make changes
git add .
git commit -m "describe your change"
git push origin your-feature-branch
```
Then open a Pull Request on GitHub into `main` rather than pushing straight to `main`.