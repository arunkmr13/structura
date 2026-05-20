# Sketchflow — Whiteboard Digitiser

> Turn hand-drawn whiteboard photos into clean, production-ready Mermaid diagrams using Gemini Vision.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-Vision-orange?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-ready-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## What it does

Upload any whiteboard photo, napkin sketch, or hand-drawn flowchart — Sketchflow preprocesses the image, sends it to Gemini Vision, extracts the diagram structure, and returns clean Mermaid code you can use anywhere.

**Input:** A photo of a whiteboard diagram  
**Output:** Mermaid code, structured JSON, visual diagram preview

---

## Demo

| Original Sketch | Extracted Diagram |
|---|---|
| Hand-drawn bubble sort flowchart | 9 nodes, 11 edges, correct logic |
| Multi-lane approval workflow | 23 nodes, full Yes/No branching |

---

## Pipeline

```
Image Upload
     │
     ▼
┌─────────────────┐
│  Preprocessor   │  OpenCV — deskew, denoise, adaptive threshold
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini Vision  │  gemini-2.5-flash → 2.0-flash → 2.0-flash-lite
│  (with fallback)│  Structured JSON extraction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Renderer     │  JSON → Mermaid syntax (graph TD)
└────────┬────────┘
         │
         ▼
    Mermaid Code + JSON + Visual Preview
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Image Processing | OpenCV, Pillow |
| Vision AI | Google Gemini (google-genai SDK) |
| Diagram Rendering | Mermaid.js v10 |
| Frontend | Vanilla HTML/CSS/JS |
| Container | Docker, Docker Compose |

---

## Project Structure

```
whiteboard-digitiser/
├── backend/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, endpoints, rate limiting, logging
│   ├── preprocessor.py   # OpenCV image cleaning pipeline
│   ├── extractor.py      # Gemini Vision API call + JSON parsing + model fallback
│   ├── renderer.py       # JSON → Mermaid code generation
│   └── logger.py         # Structured logging (console + file)
├── static/
│   ├── script.js         # Upload, digitise, tabs, toast, download logic
│   └── style.css         # Dark SaaS theme, CSS variables, responsive layout
├── templates/
│   └── index.html        # Sketchflow UI — split panel, drag-and-drop
├── .env.example          # Environment variable template
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/apikey)
- Docker (optional)

### Local Setup

**1. Clone the repo**

```bash
git clone https://github.com/arunkmr13/whiteboard-digitiser.git
cd whiteboard-digitiser
```

**2. Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your-gemini-api-key-here
```

**5. Run the server**

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000)

---

### Docker Setup

```bash
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000)

---

## API

### POST `/digitise`

Accepts a whiteboard image and returns Mermaid code + structured JSON.

**Request**
```
Content-Type: multipart/form-data
Body: file (JPEG / PNG / WebP, max 5MB)
```

**curl example**
```bash
curl -X POST http://localhost:8000/digitise \
  -F "file=@whiteboard.jpg"
```

**Python example**
```python
import requests

with open("whiteboard.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/digitise",
        files={"file": f}
    )

data = response.json()
print(data["mermaid"])      # Mermaid code
print(data["model_used"])   # Which Gemini model was used
print(data["raw"])          # Structured JSON (nodes, edges)
```

**Response**
```json
{
  "mermaid": "graph TD\n    A[\"Start\"] --> B[\"Process\"]...",
  "model_used": "gemini-2.5-flash",
  "raw": {
    "diagram_type": "flowchart",
    "title": null,
    "nodes": [
      { "id": "A", "label": "Start", "shape": "circle" }
    ],
    "edges": [
      { "from": "A", "to": "B", "label": "yes", "style": "solid" }
    ]
  }
}
```

**Error codes**

| Code | Meaning |
|---|---|
| 400 | Invalid file type or file exceeds 5MB |
| 429 | Rate limit exceeded (10 requests / 60 seconds per IP) |
| 500 | Extraction failed — JSON parse error or API error |
| 504 | Gemini API timed out |

---

## Features

- **Drag-and-drop upload** with file validation and size check
- **Image preprocessing** — denoise, grayscale, adaptive threshold via OpenCV
- **Model fallback chain** — tries `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite` automatically on failure
- **Three output tabs** — visual diagram, Mermaid code, raw JSON
- **Diagram metadata** — detects type, node count, edge count
- **Copy & download** — copy Mermaid to clipboard or download as `.md`
- **Rate limiting** — 10 requests per 60 seconds per IP (in-memory)
- **Structured logging** — console + `app.log` file
- **Retry logic** — auto-retries on 503/429 with exponential backoff
- **Responsive UI** — works on mobile and desktop

---

## Tips for Best Results

- 📸 Shoot straight-on — avoid angle distortion
- 💡 Good lighting — no glare on the whiteboard
- ✏️ Use clear shapes — boxes, diamonds, ovals
- → Draw arrows with obvious direction
- 🔤 Keep labels short and inside shapes
- 🧹 Use a clean whiteboard — erase old marks

---

## Limitations

- Complex cyclic diagrams may not render visually inline — use [mermaid.live](https://mermaid.live) for those
- Very messy or low-contrast sketches reduce extraction accuracy
- Labels with special characters are simplified to plain English
- Rate limited to 10 requests/minute per IP on the free tier

---

## Related Projects

- [docx-report-engine](https://github.com/arunkmr13/docx-report-engine)
- [text-ocr-translator](https://github.com/arunkmr13/text-ocr-translator)
- [figcaption](https://github.com/arunkmr13/figcaption)

---

## License

MIT — free to use, modify, and distribute.

---

Built by [Arun Kumar](https://github.com/arunkmr13)