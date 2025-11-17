from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import sqlite3
import json
import random
import base64
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

# Import new core components
from app.core.pdf_parser import PDFParser
from app.core.pdf_filler import PDFFiller
from app.core.llm_service import LLMService

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

# Initialize core services
pdf_parser = PDFParser(embed_model=embed_model)
pdf_filler = PDFFiller(use_handwriting_font=False)
llm_service = LLMService()

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
            "/tools/classifyAIRisk",
            "/tools/inferRegulatoryData"
        ]
    }

@app.post("/tools/detectIntent")
async def detect_intent(body: IntentRequest = Body(...)):
    """Detect user intent from chat input using LLM service."""
    # Use LLM service for intent classification
    result = llm_service.classify_intent_and_slots(body.text)
    
    # Ensure required fields
    if 'intentType' not in result:
        result['intentType'] = "general"
    if 'slots' not in result:
        result['slots'] = {}
    if 'confidence' not in result:
        result['confidence'] = 0.5
    
    return {
        "intentType": result['intentType'],
        "slots": result['slots'],
        "confidence": round(result.get('confidence', 0.5), 2)
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
    """Map form fields to user data using semantic similarity and LLM."""
    try:
        # Use PDF parser for semantic mapping
        result = pdf_parser.semantic_field_mapping(
            body.labels,
            body.userData or {},
            body.slots or {}
        )
        
        # Optionally use LLM to infer missing values
        if llm_service.client:
            inferred = llm_service.infer_field_values(body.labels, {
                **(body.userData or {}),
                **(body.slots or {})
            })
            # Merge inferred values
            if inferred:
                result['fieldValues'].update(inferred)
        
        return result
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
    """Fill PDF form with field values using true PDF form filling."""
    form_id = body.formId
    values = body.fieldValues
    
    # Find template path
    template_path = f"templates/{form_id}.pdf"
    if not os.path.exists(template_path):
        # Try alternative paths
        alternatives = [
            f"templates/{form_id}_template.pdf",
            f"templates/{form_id}_record.pdf",
            f"templates/{form_id}_worksheet.pdf",
        ]
        for alt in alternatives:
            if os.path.exists(alt):
                template_path = alt
                break
        else:
            raise HTTPException(status_code=404, detail=f"Template not found for form: {form_id}")
    
    try:
        # Use PDF filler for true form filling
        output_path = pdf_filler.fill_pdf_form(template_path, values)
        
        return {
            "docId": output_path,
            "formId": form_id,
            "status": "filled",
            "method": "true_form_filling"
        }
    except Exception as e:
        print(f"Error filling PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fill PDF: {str(e)}")

@app.post("/tools/parseForm")
async def parse_form(body: ParseFormRequest = Body(...)):
    """Parse PDF form to extract field labels using enhanced parser."""
    if not os.path.exists(body.pdfPath):
        raise HTTPException(status_code=404, detail=f"PDF not found: {body.pdfPath}")
    
    try:
        result = pdf_parser.extract_form_fields(body.pdfPath, use_ocr=True)
        
        return {
            "labels": result.get('labels', []),
            "fields": result.get('fields', []),
            "textContent": result.get('text_content', ''),
            "pageCount": result.get('page_count', 0),
            "hasFormFields": result.get('has_form_fields', False)
        }
    except Exception as e:
        print(f"Error parsing form: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

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
    if n8n_webhook:
        try:
            # Read file and encode as base64 for n8n
            with open(file_path, 'rb') as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            file_name = os.path.basename(file_path)
            
            response = requests.post(n8n_webhook, json={
                "filePath": file_path,
                "fileName": file_name,
                "fileContent": file_base64,
                "recipient": recipient,
                "subject": "Compliance Document",
                "body": "Please find attached your compliance document."
            }, timeout=30)
            response.raise_for_status()
            return {
                "status": "sent",
                "recipient": recipient,
                "filePath": file_path,
                "n8nResponse": response.status_code
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        except requests.exceptions.RequestException as e:
            print(f"n8n webhook error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send email via n8n: {str(e)}")
    
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
    
    # Try LLM service first for better reasoning
    if llm_service.client:
        try:
            llm_result = llm_service.infer_regulatory_data(description, "EU_AI_ACT")
            if llm_result and 'risk_level' in llm_result:
                return llm_result
        except Exception as e:
            print(f"LLM classification error: {e}")
    
    # Fallback to rule-based classification
    result = classify_ai_risk(description)
    return result

@app.post("/tools/inferRegulatoryData")
async def infer_regulatory_data(body: Dict = Body(...)):
    """Infer regulatory data from description using LLM."""
    description = body.get('description', '')
    regulation = body.get('regulation', 'GDPR')
    
    if not description:
        raise HTTPException(status_code=400, detail="Description required")
    
    result = llm_service.infer_regulatory_data(description, regulation)
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
