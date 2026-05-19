from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from backend.preprocessor import preprocess_image
from backend.extractor import extract_diagram
from backend.renderer import to_mermaid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/digitise")
async def digitise(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP supported")

    raw_bytes = await file.read()
    clean_bytes = preprocess_image(raw_bytes)

    try:
        diagram_data = extract_diagram(clean_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    mermaid_code = to_mermaid(diagram_data)

    return JSONResponse({
        "mermaid": mermaid_code,
        "raw": diagram_data
    })