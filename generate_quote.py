import os
import json
import requests
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- 1. FILE TEXT EXTRACTION & AI CORE ---
def extract_from_file(input_file_path):
    """Reads a text or PDF file and asks local Llama 3 to extract parameters."""
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Cannot find input file: {input_file_path}")

    if input_file_path.endswith('.pdf'):
        reader = PdfReader(input_file_path)
        raw_text = "".join([page.extract_text() or "" for page in reader.pages])
    else:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

    system_prompt = """You are an engineering assistant. Extract these exact metrics into clean JSON:
    { "flow_rate": float, "flow_unit": "USGPM" or "LPM", "inlet_temp": float, "outlet_temp": float, "wet_bulb": float }"""

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3:8b",
        "prompt": f"{system_prompt}\n\nClient Document:\n{raw_text}\n\nOutput JSON:",
        "stream": False,
        "format": "json"
    }
    
    response = requests.post(url, json=payload)
    return json.loads(response.json()['response'])

# --- 2. ENGINEERING CALCULATIONS ENGINE ---
def calculate_required_tr(conditions):
    """Applies your approach/range thumb rules to compute required Tonnage."""
    inlet = conditions.get("inlet_temp", 37)
    outlet = conditions.get("outlet_temp", 32)
    wb = conditions.get("wet_bulb", 28)
    flow = conditions.get("flow_rate", 170)

    # Upper/Lower bound rule mapping
    if wb == 28 and outlet == 32 and inlet <= 38:
        gpm_per_ton = 4.0
    else:
        gpm_per_ton = 3.5

    calculated_tr = flow / gpm_per_ton if flow else 0
    return calculated_tr

# --- 3. STANDALONE PDF GENERATOR ---
def generate_result_pdf(input_file_path):
    # Execute AI Extraction
    conditions = extract_from_file(input_file_path)
    print(f"🤖 Extracted Parameters: {conditions}")
    
    # Calculate Tonnage
    computed_tr = calculate_required_tr(conditions)
    print(f"🧮 Calculated Target Capacity: {computed_tr:.0f} TR")
    
    # Generate a clean, brand new PDF file from scratch
    output_filename = "result.pdf"
    c = canvas.Canvas(output_filename, pagesize=letter)
    
    # Structural Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 730, "Cooling Tower Selection Summary")
    c.setLineWidth(1)
    c.line(50, 715, 550, 715)
    
    # Output the exact TR Requirement clearly
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.05, 0.25, 0.45) # Professional Navy Text Color
    c.drawString(50, 670, f"Suggested Tower Capacity: {computed_tr:.0f} TR")
    
    # Optional metadata baseline just for confirmation
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(50, 640, f"Based on: {conditions.get('flow_rate')} {conditions.get('flow_unit')} @ WBT {conditions.get('wet_bulb')}°C")
    
    c.save()
    print(f"📄 Success! Standalone file saved as: {output_filename}")

if __name__ == "__main__":
    # Point this to your test_client_inquiry.txt or any incoming inquiry 
    generate_result_pdf("test_client_inquiry.txt")