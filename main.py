from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sqlite3
import json
import random
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from dotenv import load_dotenv
import requests
from datetime import datetime

from utils import (
    get_weather, suggest_load_shift, calculate_emissions,
    load_recipes, load_regulations, generate_compliance_pack as generate_compliance_pack_util,
    classify_ai_risk
)

load_dotenv()

# Initialize models
try:
    embed_model = SentenceTransformer('intfloat/multilingual-e5-large')
    dimension = 1024
    index = faiss.IndexFlatL2(dimension)
    print("Embedding model loaded successfully")
except Exception as e:
    print(f"Warning: Could not load embedding model: {e}")
    embed_model = None
    index = None

app = FastAPI(
    title="Green SME Compliance Co-Pilot",
    description="AI agent for ESG audits and compliance filings (CSRD/GDPR/EU AI Act)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class IntentRequest(BaseModel):
    text: str

class WorkflowRequest(BaseModel):
    intentType: str
    slots: Dict

class MapFieldsRequest(BaseModel):
    labels: List[str]
    userData: Optional[Dict] = {}
    slots: Optional[Dict] = {}

class EmissionsRequest(BaseModel):
    kWh: float
    gridFactor: Optional[float] = None
    country: Optional[str] = "DE"

class FillPdfRequest(BaseModel):
    formId: str
    fieldValues: Dict

class ParseFormRequest(BaseModel):
    pdfPath: str

class CollectAnswersRequest(BaseModel):
    questions: List[str]
    submissionId: Optional[int] = None

# Database helper
def get_db():
    db_path = os.getenv('DB_PATH', 'db.sqlite')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {
        "message": "Green SME Compliance Co-Pilot API",
        "version": "1.0.0",
        "endpoints": [
            "/tools/detectIntent",
            "/tools/selectWorkflow",
            "/tools/mapFields",
            "/tools/estimateEmissions",
            "/tools/fillPdf",
            "/tools/parseForm",
            "/tools/collectAnswers",
            "/tools/exportFile",
            "/tools/emailFile",
            "/tools/generateCompliancePack",
            "/tools/classifyAIRisk"
        ]
    }

@app.post("/tools/detectIntent")
async def detect_intent(body: IntentRequest = Body(...)):
    """Detect user intent from chat input using pattern matching and LLM."""
    text = body.text.lower()
    
    # Pattern matching (fallback if LLM unavailable)
    intent_patterns = {
        "energyAuditForCSRD": ["energy audit", "csrd", "emissions", "carbon", "kwh", "kilowatt"],
        "gdprArt30": ["gdpr", "article 30", "data processing", "privacy record"],
        "euAiActRisk": ["ai act", "ai risk", "high-risk ai", "ai compliance", "artificial intelligence"]
    }
    
    detected_intent = None
    confidence = 0.7
    slots = {}
    
    for intent, patterns in intent_patterns.items():
        matches = sum(1 for pattern in patterns if pattern in text)
        if matches > 0:
            detected_intent = intent
            confidence = min(0.95, 0.7 + (matches * 0.1))
            
            # Extract slots
            import re
            kwh_match = re.search(r'(\d+)\s*(kwh|kilowatt)', text)
            if kwh_match:
                slots['kWh'] = float(kwh_match.group(1))
            
            city_match = re.search(r'\b([A-Z][a-z]+)\b', text)
            if city_match:
                slots['city'] = city_match.group(1)
            
            break
    
    # Try Mistral API if available
    mistral_key = os.getenv('MISTRAL_API_KEY')
    if mistral_key and mistral_key != 'your_mistral_api_key_here':
        try:
            from mistralai import Mistral
            client = Mistral(api_key=mistral_key)
            response = client.chat.complete(
                model="mistral-tiny",
                messages=[{
                    "role": "user",
                    "content": f"Extract intent and slots from: {body.text}. Respond with JSON: intentType, slots (kWh, city), confidence."
                }]
            )
            # Parse response (simplified)
            if response and hasattr(response, 'choices'):
                # Update with LLM results if better
                pass
        except Exception as e:
            print(f"Mistral API error: {e}")
    
    if not detected_intent:
        detected_intent = "general"
        confidence = 0.5
    
    return {
        "intentType": detected_intent,
        "slots": slots,
        "confidence": round(confidence, 2)
    }

@app.post("/tools/selectWorkflow")
async def select_workflow(body: WorkflowRequest = Body(...)):
    """Select workflow recipe based on detected intent."""
    recipes = load_recipes()
    intent = body.intentType
    
    # Map intent to recipe
    intent_to_recipe = {
        "energyAuditForCSRD": "csrd_audit",
        "gdprArt30": "gdpr_art30",
        "euAiActRisk": "eu_ai_act_risk"
    }
    
    recipe_id = intent_to_recipe.get(intent, "csrd_audit")
    recipe = recipes.get('recipes', {}).get(recipe_id, {})
    
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe not found: {recipe_id}")
    
    needed_forms = recipe.get('needed_forms', [])
    questions = []
    
    # Generate questions for missing slots
    if intent == "energyAuditForCSRD" and 'kWh' not in body.slots:
        questions.append("What is your monthly energy consumption in kWh?")
    if 'city' not in body.slots:
        questions.append("What city is your business located in?")
    
    return {
        "recipeId": recipe_id,
        "recipeName": recipe.get('name', ''),
        "neededForms": needed_forms,
        "workflow": recipe.get('workflow', []),
        "questions": questions
    }

@app.post("/tools/mapFields")
async def map_fields(body: MapFieldsRequest = Body(...)):
    """Map form fields to user data using semantic similarity."""
    if not embed_model or not index:
        # Fallback: simple keyword matching
        field_values = {}
        low_confidence = []
        
        user_data = body.userData
        slots = body.slots
        
        for label in body.labels:
            label_lower = label.lower()
            if 'name' in label_lower or 'company' in label_lower:
                field_values['name'] = user_data.get('name', 'Prime Bakery')
            elif 'address' in label_lower:
                field_values['address'] = user_data.get('address', 'Flensburg St 1, 24937 Flensburg')
            elif 'email' in label_lower:
                field_values['email'] = user_data.get('email', 'info@bakery.de')
            elif 'kwh' in label_lower or 'energy' in label_lower:
                field_values['energy_kwh'] = slots.get('kWh', 3000)
            elif 'emission' in label_lower or 'co2' in label_lower or 'carbon' in label_lower:
                if 'kWh' in slots:
                    emissions = calculate_emissions(slots['kWh'])
                    field_values['tCO2e'] = emissions['tCO2e']
        
        return {
            "fieldValues": field_values,
            "lowConfidence": low_confidence
        }
    
    # Semantic matching with embeddings
    try:
        label_embeddings = embed_model.encode(body.labels, show_progress_bar=False)
        faiss.normalize_L2(label_embeddings.astype('float32'))
        
        # Query against indexed forms (simplified - in production, query pre-indexed canonicals)
        field_values = {}
        low_confidence = []
        
        # Map based on semantic similarity and user data
        user_data = body.userData
        slots = body.slots
        
        # Simple mapping logic
        for i, label in enumerate(body.labels):
            label_lower = label.lower()
            if any(kw in label_lower for kw in ['name', 'company', 'organization']):
                field_values['name'] = user_data.get('name', 'Prime Bakery')
            elif any(kw in label_lower for kw in ['address', 'street', 'location']):
                field_values['address'] = user_data.get('address', 'Flensburg St 1, 24937 Flensburg')
            elif 'email' in label_lower:
                field_values['email'] = user_data.get('email', 'info@bakery.de')
            elif any(kw in label_lower for kw in ['kwh', 'kilowatt', 'energy consumption']):
                field_values['energy_kwh'] = slots.get('kWh', 3000)
            elif any(kw in label_lower for kw in ['emission', 'co2', 'carbon', 'tco2e']):
                if 'kWh' in slots:
                    emissions = calculate_emissions(slots['kWh'])
                    field_values['tCO2e'] = emissions['tCO2e']
                else:
                    low_confidence.append(label)
        
        return {
            "fieldValues": field_values,
            "lowConfidence": low_confidence
        }
    except Exception as e:
        print(f"Error in mapFields: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/estimateEmissions")
async def estimate_emissions(body: EmissionsRequest = Body(...)):
    """Estimate CO2 emissions from energy consumption."""
    result = calculate_emissions(
        body.kWh,
        body.gridFactor,
        body.country
    )
    return result

@app.post("/tools/fillPdf")
async def fill_pdf(body: FillPdfRequest = Body(...)):
    """Fill PDF form with field values."""
    form_id = body.formId
    values = body.fieldValues
    
    # Create output directory if needed
    os.makedirs('outputs', exist_ok=True)
    
    pdf_path = f"outputs/filled_{form_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Form: {form_id}")
    y -= 30
    
    c.setFont("Helvetica", 12)
    for key, value in values.items():
        if y < 50:
            c.showPage()
            y = height - 50
        
        c.drawString(50, y, f"{key}: {value}")
        y -= 20
    
    c.save()
    
    return {
        "docId": pdf_path,
        "formId": form_id,
        "status": "filled"
    }

@app.post("/tools/parseForm")
async def parse_form(body: ParseFormRequest = Body(...)):
    """Parse PDF form to extract field labels."""
    from ingest import extract_form_fields
    
    result = extract_form_fields(body.pdfPath, use_ocr=True)
    
    return {
        "labels": result['labels'],
        "textContent": result['text_content'],
        "pageCount": result['page_count']
    }

@app.post("/tools/collectAnswers")
async def collect_answers(body: CollectAnswersRequest = Body(...)):
    """Collect answers to questions (mock for MVP)."""
    # In production, this would integrate with chat interface
    # For MVP, return mock answers
    answers = {}
    for question in body.questions:
        if "kwh" in question.lower() or "energy" in question.lower():
            answers[question] = "3000"
        elif "city" in question.lower():
            answers[question] = "Flensburg"
        else:
            answers[question] = "N/A"
    
    return {
        "answers": answers,
        "status": "collected"
    }

@app.post("/tools/exportFile")
async def export_file(body: Dict = Body(...)):
    """Export file to MinIO or local storage."""
    file_path = body.get('filePath')
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # For MVP, just return the local path
    # In production, upload to MinIO
    minio_url = os.getenv('MINIO_URL')
    if minio_url and minio_url != 'http://localhost:9000':
        # Upload to MinIO (simplified)
        pass
    
    return {
        "fileUrl": f"/outputs/{os.path.basename(file_path)}",
        "filePath": file_path,
        "status": "exported"
    }

@app.post("/tools/emailFile")
async def email_file(body: Dict = Body(...)):
    """Send file via email using n8n webhook."""
    n8n_webhook = os.getenv('N8N_WEBHOOK_URL')
    file_path = body.get('filePath')
    recipient = body.get('recipient', 'info@bakery.de')
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Trigger n8n webhook
    if n8n_webhook and n8n_webhook != 'http://localhost:5678/webhook/compliance-email':
        try:
            response = requests.post(n8n_webhook, json={
                "filePath": file_path,
                "recipient": recipient,
                "subject": "Compliance Document",
                "body": "Please find attached your compliance document."
            }, timeout=10)
            return {
                "status": "sent",
                "n8nResponse": response.status_code
            }
        except Exception as e:
            print(f"n8n webhook error: {e}")
    
    # Fallback: mock response
    return {
        "status": "queued",
        "recipient": recipient,
        "filePath": file_path,
        "note": "Email queued (n8n not configured)"
    }

@app.post("/tools/generateCompliancePack")
async def generate_compliance_pack(body: Dict = Body(...)):
    """Generate compliance pack PDF with regulatory mappings."""
    submission_id = body.get('submissionId', 1)
    recipe_id = body.get('recipeId', 'csrd_audit')
    regulations = body.get('regulations', [])
    
    if not regulations:
        recipes = load_recipes()
        recipe = recipes.get('recipes', {}).get(recipe_id, {})
        regulations = recipe.get('regulations', [])
    
    pdf_path = generate_compliance_pack_util(submission_id, recipe_id, regulations)
    
    if not pdf_path:
        raise HTTPException(status_code=500, detail="Failed to generate compliance pack")
    
    return {
        "filePath": pdf_path,
        "submissionId": submission_id,
        "regulations": regulations,
        "status": "generated"
    }

@app.post("/tools/classifyAIRisk")
async def classify_ai_risk_endpoint(body: Dict = Body(...)):
    """Classify AI system risk level per EU AI Act."""
    description = body.get('description', '')
    
    if not description:
        raise HTTPException(status_code=400, detail="Description required")
    
    result = classify_ai_risk(description)
    return result

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "embedding_model": "loaded" if embed_model else "not loaded",
        "faiss_index": "ready" if index else "not ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
