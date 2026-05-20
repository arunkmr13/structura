import os
import json
import re
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Fallback chain — tries in order
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

PROMPT = """
You are a diagram parser. Analyze this whiteboard image carefully.

Return a JSON object with exactly these fields:
{
  "diagram_type": "flowchart",
  "title": null,
  "nodes": [
    { "id": "A", "label": "Step name", "shape": "rect" }
  ],
  "edges": [
    { "from": "A", "to": "B", "label": "", "style": "solid" }
  ]
}

STRICT RULES:
- Node ids must be simple letters or short alphanumeric strings like A, B, C or N1, N2
- Labels must be plain text only — no special characters like < > [ ] { } ( ) = + - /
- Replace any math or code expressions with plain English:
  e.g. "i <= length(A)-2" becomes "i less than length"
  e.g. "A[i] > A[i+1]" becomes "A i greater than A i plus 1"
  e.g. "swap(A[i], A[i+1])" becomes "swap elements"
- Edge labels should be simple words like "yes", "no", "true", "false"
- Return ONLY valid JSON, no explanation, no markdown fences
- Every string value must use double quotes
"""

def _parse_response(raw: str) -> dict:
    raw = raw.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()

    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON: {e}\nRaw: {raw[:300]}")


def _call_model(model: str, image_bytes: bytes) -> dict:
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            PROMPT
        ]
    )
    return _parse_response(response.text)


def extract_diagram(image_bytes: bytes) -> tuple:
    last_error = None

    for model in MODELS:
        try:
            result = _call_model(model, image_bytes)
            return result, model

        except Exception as e:
            last_error = e
            err_str = str(e)

            is_retryable = any(code in err_str for code in [
                "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED",
                "500", "INTERNAL", "timeout", "Timeout"
            ])

            is_not_found = "404" in err_str or "NOT_FOUND" in err_str

            if is_retryable and not is_not_found:
                time.sleep(1.5)
                continue
            else:
                raise

    raise RuntimeError(f"All models failed. Last error: {last_error}")