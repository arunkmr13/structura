import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

def extract_diagram(image_bytes: bytes) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            PROMPT
        ]
    )

    raw = response.text.strip()

    # Strip markdown fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()

    # Remove any control characters that break JSON
    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to extract JSON object from response if there's surrounding text
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from Gemini response: {e}\nRaw: {raw[:300]}")