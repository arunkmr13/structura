import os
import re
import json
import base64
from io import BytesIO
from rdkit import Chem
from rdkit.Chem import Draw, AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

FORMULA_PROMPT = """
You are a chemistry expert. Given a chemical formula or name, return a JSON object.

Return ONLY this JSON, no explanation, no markdown fences:
{
  "smiles": "canonical SMILES string",
  "iupac_name": "official IUPAC name",
  "common_name": "common name if exists, else null",
  "molecular_formula": "e.g. CH4",
  "molecular_weight": "e.g. 16.04 g/mol",
  "bond_count": 4,
  "atom_count": 5,
  "description": "one sentence describing the molecule"
}

Rules:
- smiles must be a valid canonical SMILES string
- If the input is ambiguous or not a real molecule, return {"error": "description of problem"}
- Never guess — if unsure about the SMILES, return an error
"""

def _call_gemini(prompt_text: str) -> dict:
    last_error = None

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[prompt_text]
            )

            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                raw = raw.rsplit("```", 1)[0].strip()

            data = json.loads(raw)

            if "error" in data:
                raise ValueError(data["error"])

            return data, model

        except (json.JSONDecodeError, ValueError) as e:
            raise
        except Exception as e:
            last_error = e
            err_str = str(e)
            is_retryable = any(c in err_str for c in [
                "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500"
            ])
            if is_retryable:
                import time
                time.sleep(1.5)
                continue
            raise

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def smiles_to_image(smiles: str, style: str = "skeletal") -> str:
    """Convert SMILES to a base64 PNG image."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    # Add hydrogens for Lewis style
    if style == "lewis":
        mol = Chem.AddHs(mol)
        AllChem.Compute2DCoords(mol)
    else:
        AllChem.Compute2DCoords(mol)

    # Draw
    drawer = rdMolDraw2D.MolDraw2DSVG(600, 400)
    drawer.drawOptions().addStereoAnnotation = True
    drawer.drawOptions().addAtomIndices = False

    if style == "lewis":
        drawer.drawOptions().explicitMethyl = True

    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()

    # Convert SVG to PNG via cairosvg
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(bytestring=svg.encode(), output_width=600, output_height=400)
    except Exception:
        # Fallback: return SVG as base64 if cairosvg fails
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

    return "data:image/png;base64," + base64.b64encode(png_bytes).decode()


def process_formula(formula: str, style: str = "skeletal") -> dict:
    """Full pipeline: formula → Gemini → SMILES → image."""

    # Get molecule data from Gemini
    prompt = f"{FORMULA_PROMPT}\n\nInput: {formula}"
    mol_data, model_used = _call_gemini(prompt)

    smiles = mol_data.get("smiles")
    if not smiles:
        raise ValueError("No SMILES returned from model")

    # Validate SMILES with RDKit
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Generated SMILES is invalid: {smiles}")

    # Generate image
    image_data = smiles_to_image(smiles, style)

    return {
        "image": image_data,
        "smiles": smiles,
        "model_used": model_used,
        "metadata": {
            "iupac_name":       mol_data.get("iupac_name"),
            "common_name":      mol_data.get("common_name"),
            "molecular_formula": mol_data.get("molecular_formula"),
            "molecular_weight": mol_data.get("molecular_weight"),
            "bond_count":       mol_data.get("bond_count"),
            "atom_count":       mol_data.get("atom_count"),
            "description":      mol_data.get("description"),
        }
    }