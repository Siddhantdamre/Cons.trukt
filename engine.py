import os
from google import genai
from pydantic import BaseModel

client = genai.Client(api_key="YOUR_API_KEY")

# Define the structure for the industrial output
class SmartTaskSchema(BaseModel):
    wbs_code: str
    name: str
    materials: list[str]
    estimated_hours: int

def parse_blueprint(file_path):
    """Parses blueprint PDF into structured Industrial JSON"""
    doc = client.files.upload(path=file_path)
    prompt = "Extract the Bill of Quantities. Format as JSON with WBS codes."
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[doc, prompt],
        config={'response_mime_type': 'application/json'}
    )
    
    return response.text

# Example execution:
# tasks = parse_blueprint("site_plan_v1.pdf")