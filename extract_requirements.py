import os
import requests
import json
from pypdf import PdfReader

SYSTEM_PROMPT = """You are an engineering assistant for Delta Cooling Towers. Your sole job is to extract raw design parameters from messy customer inquiries into structured JSON.

CRITICAL INSTRUCTIONS:
1. Extract Flow Rate (always try to find USGPM or LPM).
2. Extract Water Temperatures (Inlet/Hot Water, Outlet/Cold Water, and Wet Bulb temperature).
3. IGNORE any explicit tonnage or physical tower size dimensions mentioned by the user.

Expected JSON Structure:
{
  "flow_rate": float or null,
  "flow_unit": "USGPM" or "LPM" or null,
  "inlet_temp": float or null,
  "outlet_temp": float or null,
  "wet_bulb": float or null
}
"""

def read_input_file(file_path):
    """Reads text from a .txt or .pdf file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No file found at {file_path}")
    
    if file_path.endswith('.pdf'):
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def extract_design_conditions(file_path):
    print(f"📂 Reading incoming customer file: {file_path}...")
    raw_text = read_input_file(file_path)
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3:8b",
        "prompt": f"{SYSTEM_PROMPT}\n\nClient Inquiry File Content:\n\"\"\"{raw_text}\"\"\"\n\nOutput JSON:",
        "stream": False,
        "format": "json"
    }
#important to add 
    try:
        response = requests.post(url, json=payload)
        return json.loads(response.json()['response'])
    except Exception as e:
        print(f"❌ AI Extraction Error: {e}")
        return None