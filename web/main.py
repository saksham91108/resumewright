import os
import sys
import shutil
import tempfile
import time
import uuid
import zipfile
import io

# Allow importing extractor.py, validator.py, etc. from the parent project folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

from extractor import extract_text, ExtractionError
from validator import validate_and_clean, check_file_exists, ValidationError
from gemini_client import generate_content, GeminiConfigError, GeminiAPIError
from prompt_builder import build_prompt
from json_processor import process_gemini_response, JSONParseError

app = FastAPI(title="resumewright")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
pages = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Vercel's filesystem is read-only except /tmp — use /tmp there, "web_output" locally.
OUTPUT_DIR = "/tmp/outputs" if os.environ.get("VERCEL") else os.path.join(BASE_DIR, "web_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PORTFOLIO_TEMPLATES_DIR = os.path.join(BASE_DIR, "..", "templates")  # your existing templates1-4 folder

# Maps the frontend's word-slug values to your existing templateN folders
TEMPLATE_SLUGS = {
    "ledger": "template1",
    "terminal": "template2",
    "signal": "template3",
    "dynamic": "template4",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB, matches frontend's stated limit


ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return pages.TemplateResponse(request, "index.html", {"error": None})


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    resume: UploadFile = File(...),
    template: str = Form("ledger"),
):
    start_time = time.monotonic()

    def error_page(message: str, status_code: int = 400):
        return pages.TemplateResponse(
            request,
            "index.html",
            {"error": message},
            status_code=status_code,
        )

    if template not in TEMPLATE_SLUGS:
        return error_page("Invalid template selection.")

    filename_lower = (resume.filename or "").lower()
    if not resume.filename or not filename_lower.endswith(ALLOWED_EXTENSIONS):
        return error_page("Please upload a .pdf, .docx, or .txt file.")

    contents = await resume.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        return error_page("File over 10mb.")

    original_filename = resume.filename

    upload_ext = os.path.splitext(filename_lower)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=upload_ext) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        check_file_exists(tmp_path)
        raw_text = extract_text(tmp_path)
        cleaned_text = validate_and_clean(raw_text)
        prompt = build_prompt(cleaned_text)
        gemini_response = generate_content(prompt)
        data = process_gemini_response(gemini_response)

        job_id = uuid.uuid4().hex[:10]
        job_dir = os.path.join(OUTPUT_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        template_folder = TEMPLATE_SLUGS[template]
        template_dir = os.path.join(PORTFOLIO_TEMPLATES_DIR, template_folder)
        env = Environment(loader=FileSystemLoader(template_dir))
        rendered = env.get_template("portfolio_template.html").render(**data)

        output_filename = "portfolio.html"
        with open(os.path.join(job_dir, output_filename), "w", encoding="utf-8") as f:
            f.write(rendered)

        css_source = os.path.join(template_dir, "style.css")
        if os.path.exists(css_source):
            shutil.copy(css_source, os.path.join(job_dir, "style.css"))

        elapsed = time.monotonic() - start_time
        duration_str = f"{elapsed:.1f}s"
        portfolio_url = f"/view/{job_id}/{output_filename}"

        return pages.TemplateResponse(
            request,
            "result.html",
            {
                "job_id": job_id,
                "filename": output_filename,
                "template": template,
                "portfolio_url": portfolio_url,
                "duration": duration_str,
                "name": data.get("name", "your"),
            },
        )

    except ValidationError as e:
        return error_page(str(e))
    except ExtractionError as e:
        return error_page(f"Could not read this PDF: {e}")
    except GeminiConfigError as e:
        return error_page(f"Server configuration error: {e}", status_code=500)
    except GeminiAPIError as e:
        return error_page(f"AI service error, please try again: {e}", status_code=502)
    except JSONParseError as e:
        return error_page(f"Could not process the AI response: {e}", status_code=502)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/view/{job_id}/{filename}")
async def view_output(job_id: str, filename: str):
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    file_path = os.path.join(job_dir, filename)
    if not os.path.isfile(file_path):
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(file_path)


@app.get("/download/{job_id}/{filename}")
async def download_output(job_id: str, filename: str):
    """Download the full portfolio (HTML + CSS) as a single zip so styling isn't lost."""
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    if not os.path.isdir(job_dir):
        return HTMLResponse("Not found", status_code=404)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(job_dir):
            fpath = os.path.join(job_dir, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, arcname=fname)
    buffer.seek(0)

    zip_name = "portfolio.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )