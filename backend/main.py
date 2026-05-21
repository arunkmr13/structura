from backend.chemistry import process_formula
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from collections import defaultdict
import time

from backend.preprocessor import preprocess_image
from backend.extractor import extract_diagram
from backend.renderer import to_mermaid
from backend.logger import get_logger
logger = get_logger("main")

app = FastAPI()

# In-memory rate limiter — 10 requests per 60 seconds per IP
RATE_LIMIT = 10
WINDOW_SECONDS = 60
request_log: dict = defaultdict(list)

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    timestamps = request_log[ip]
    # Remove timestamps outside the window
    request_log[ip] = [t for t in timestamps if now - t < WINDOW_SECONDS]
    if len(request_log[ip]) >= RATE_LIMIT:
        return True
    request_log[ip].append(now)
    return False

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/digitise")
async def digitise(request: Request, file: UploadFile = File(...)):
    ip = request.client.host

    if is_rate_limited(ip):
        logger.warning(f"Rate limit hit | ip={ip}")
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP supported")

    raw_bytes = await file.read()
    size_kb = len(raw_bytes) // 1024
    logger.info(f"Upload received | ip={ip} | size={size_kb}KB | type={file.content_type}")

    if len(raw_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")

    clean_bytes = preprocess_image(raw_bytes)

    try:
        diagram_data, model_used = extract_diagram(clean_bytes)
        logger.info(f"Extraction success | ip={ip} | model={model_used} | nodes={len(diagram_data.get('nodes', []))}")
    except Exception as e:
        logger.error(f"Extraction failed | ip={ip} | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    mermaid_code = to_mermaid(diagram_data)

    return JSONResponse({
        "mermaid": mermaid_code,
        "raw": diagram_data,
        "model_used": model_used
    })

from pydantic import BaseModel

class FormulaRequest(BaseModel):
    formula: str
    style: str = "skeletal"

@app.post("/chemistry")
async def chemistry(request: Request, body: FormulaRequest):
    ip = request.client.host
    if is_rate_limited(ip):
        logger.warning(f"Rate limit hit | ip={ip}")
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")

    formula = body.formula.strip()
    if not formula:
        raise HTTPException(status_code=400, detail="Formula cannot be empty")

    if len(formula) > 200:
        raise HTTPException(status_code=400, detail="Formula too long — max 200 characters")

    logger.info(f"Chemistry request | ip={ip} | formula={formula} | style={body.style}")

    try:
        result = process_formula(formula, body.style)
        logger.info(f"Chemistry success | ip={ip} | model={result['model_used']} | smiles={result['smiles']}")
        return JSONResponse(result)
    except ValueError as e:
        logger.error(f"Chemistry validation error | ip={ip} | error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chemistry failed | ip={ip} | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process formula: {str(e)}")