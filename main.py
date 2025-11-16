from fastapi import FastAPI, Body, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sentence_transformers import SentenceTransformer
import faiss
import sqlite3
import os
import random
import json
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import pypdf
import pytesseract
from PIL import Image
import io
import yaml

from utils import (
    get_weather, suggest_load_shift, generate_compliance_pack,
    estimate_emissions, send_email_via_n8n, load_compliance_matrix
)

load_dotenv()

app = FastAPI(
    title="Green SME Compliance Co-Pilot API",
    description="AI agent for ESG audits and compliance filings (CSRD/GDPR/EU AI Act)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embed_model = None
faiss_index = None
dimension = 1024

def init_models():
    global embed_model, faiss_index
    try:
        embed_model = SentenceTransformer('intfloat/multilingual-e5-large')
        faiss_index = faiss.IndexFlatL2(dimension)
        print("Models loaded successfully")
    except Exception as e:
        print(f"Model loading error: {e}")
        embed_model = None
        faiss_index = None

init_models()

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
            "/workflow/execute"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "ok"
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    model_status = "loaded" if embed_model is not None else "not loaded"
    
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status,
        "models": model_status,
        "version": "1.0.0"
    }

@app.post("/tools/detectIntent")
async def detect_intent(body: dict = Body(...)):
    """Detect user intent from chat input"""
    text = body.get('text', '')
    
    if not text:
        raise HTTPException(status_code=400, detail="Text field required")
    
    intent_keywords = {
        "energyAuditForCSRD": ["energy", "audit", "csrd", "emissions", "kwh", "consumption"],
        "gdprArticle30": ["gdpr", "article 30", "data processing", "controller", "privacy"],
        "euAIActRisk": ["ai act", "risk", "high-risk", "ai system", "transparency"]
    }
    
    text_lower = text.lower()
    detected_intent = None
    confidence = 0.0
    slots = {}
    
    for intent, keywords in intent_keywords.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            conf = matches / len(keywords)
            if conf > confidence:
                confidence = conf
                detected_intent = intent
    
    if not detected_intent:
        detected_intent = "energyAuditForCSRD"
        confidence = 0.5
    
    if "kwh" in text_lower or "kilowatt" in text_lower:
        kwh_match = re.search(r'(\d+)\s*(?:kwh|kilowatt)', text_lower)
        if kwh_match:
            slots['kWh'] = int(kwh_match.group(1))
    
    if "flensburg" in text_lower or "city" in text_lower:
        city_match = re.search(r'(\w+)', text_lower.split('city')[1] if 'city' in text_lower else '')
        slots['city'] = 'Flensburg'
    
    return {
        "intentType": detected_intent,
        "slots": slots,
        "confidence": round(confidence, 2),
        "rawText": text
    }

@app.post("/tools/selectWorkflow")
async def select_workflow(body: dict = Body(...)):
    """Select workflow recipe based on intent"""
    intent = body.get('intentType', '')
    slots = body.get('slots', {})
    
    recipes = {
        "energyAuditForCSRD": {
            "recipeId": "csrd_audit",
            "neededForms": ["vsme_snapshot", "disclosure_letter"],
            "questions": ["last_month_kWh"] if 'kWh' not in slots else [],
            "regulations": ["CSRD VSME", "ESRS E1"]
        },
        "gdprArticle30": {
            "recipeId": "gdpr_art30",
            "neededForms": ["gdpr_art30_record"],
            "questions": ["data_categories", "processing_purposes", "recipients"],
            "regulations": ["GDPR Art.30"]
        },
        "euAIActRisk": {
            "recipeId": "ai_act_check",
            "neededForms": ["ai_act_risk_worksheet"],
            "questions": ["ai_system_purpose", "data_types", "risk_level"],
            "regulations": ["EU AI Act"]
        }
    }
    
    recipe = recipes.get(intent, recipes["energyAuditForCSRD"])
    
    return {
        "recipeId": recipe["recipeId"],
        "neededForms": recipe["neededForms"],
        "questions": recipe["questions"],
        "regulations": recipe["regulations"]
    }

@app.post("/tools/mapFields")
async def map_fields(body: dict = Body(...)):
    """Map form fields using semantic embeddings"""
    labels = body.get('labels', [])
    user_profile = body.get('userProfile', {})
    slots = body.get('slots', {})
    
    if not labels:
        raise HTTPException(status_code=400, detail="Labels field required")
    
    field_values = {}
    low_confidence = []
    
    if embed_model:
        try:
            label_texts = [str(label) for label in labels if label]
            if label_texts:
                label_emb = embed_model.encode(label_texts, normalize_embeddings=True)
                
                canonical_fields = {
                    "postalCode": ["postal code", "zip", "plz", "postcode"],
                    "streetAddress": ["street", "address", "strasse", "adresse"],
                    "tCO2e": ["co2", "emissions", "carbon", "tco2"],
                    "kWh": ["kilowatt", "energy", "consumption", "kwh"],
                    "companyName": ["company", "firm", "name", "unternehmen"]
                }
                
                for field_name, synonyms in canonical_fields.items():
                    canon_emb = embed_model.encode(synonyms, normalize_embeddings=True)
                    similarities = []
                    for label_emb_vec in label_emb:
                        sim = max([faiss.METRIC_INNER_PRODUCT if hasattr(faiss, 'METRIC_INNER_PRODUCT') else 
                                  sum(label_emb_vec * canon_emb_vec) for canon_emb_vec in canon_emb])
                        similarities.append(sim)
                    
                    if similarities and max(similarities) > 0.7:
                        if field_name == "postalCode":
                            field_values[field_name] = user_profile.get('address', '').split()[-1] if user_profile.get('address') else "24937"
                        elif field_name == "tCO2e" and slots.get('kWh'):
                            emissions = estimate_emissions(slots['kWh'])
                            field_values[field_name] = emissions['tCO2e']
        except Exception as e:
            print(f"Embedding error: {e}")
    
    if not field_values.get('postalCode'):
        field_values['postalCode'] = "24937"
    
    if slots.get('kWh') and not field_values.get('tCO2e'):
        emissions = estimate_emissions(slots['kWh'])
        field_values['tCO2e'] = emissions['tCO2e']
    
    if random.random() > 0.8:
        low_confidence.append("streetAddress")
    
    return {
        "fieldValues": field_values,
        "lowConfidence": low_confidence,
        "mappedFields": len(field_values)
    }

@app.post("/tools/estimateEmissions")
async def estimate_emissions_endpoint(body: dict = Body(...)):
    """Estimate CO2 emissions from energy consumption"""
    kwh = body.get('kWh')
    grid_factor = body.get('gridFactor')
    country = body.get('country', 'DE')
    
    if not kwh:
        raise HTTPException(status_code=400, detail="kWh field required")
    
    result = estimate_emissions(kwh, grid_factor, country)
    return result

@app.post("/tools/fillPdf")
async def fill_pdf(body: dict = Body(...)):
    """Fill PDF form with mapped field values"""
    form_id = body.get('formId', 'generic_form')
    field_values = body.get('fieldValues', {})
    form_type = body.get('formType', 'vsme_snapshot')
    
    pdf_path = f"filled_{form_id}_{form_type}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Form: {form_type.upper()}")
    y -= 30
    
    c.setFont("Helvetica", 12)
    for key, value in field_values.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    
    c.save()
    
    return {
        "docId": pdf_path,
        "formId": form_id,
        "formType": form_type,
        "fieldsFilled": len(field_values)
    }

@app.post("/tools/parseForm")
async def parse_form(file: UploadFile = File(...)):
    """Parse uploaded PDF form using OCR"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    
    try:
        pdf_bytes = await file.read()
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        
        labels = []
        
        for page_num, page in enumerate(reader.pages[:3]):
            try:
                img_byte_arr = io.BytesIO()
                page_obj = page
                if hasattr(page_obj, 'to_image'):
                    img = page_obj.to_image(resolution=150)
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    
                    pil_img = Image.open(img_byte_arr)
                    ocr_data = pytesseract.image_to_data(pil_img, output_type='dict')
                    text_items = [item for item in ocr_data.get('text', []) if item.strip()]
                    labels.extend(text_items)
            except Exception as e:
                print(f"OCR error on page {page_num}: {e}")
                text = page.extract_text()
                if text:
                    labels.extend([line.strip() for line in text.split('\n') if line.strip()])
        
        return {
            "labels": labels[:50],
            "pageCount": len(reader.pages),
            "method": "OCR" if labels else "text extraction"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Form parsing error: {str(e)}")

@app.post("/tools/collectAnswers")
async def collect_answers(body: dict = Body(...)):
    """Collect answers for missing fields"""
    questions = body.get('questions', [])
    existing_answers = body.get('existingAnswers', {})
    
    mock_answers = {
        "last_month_kWh": 3000,
        "data_categories": "Customer data, employee data",
        "processing_purposes": "Order fulfillment, payroll",
        "recipients": "Payment processors, cloud providers",
        "ai_system_purpose": "Form filling assistance",
        "data_types": "Structured form data",
        "risk_level": "Low"
    }
    
    answers = {}
    for q in questions:
        answers[q] = mock_answers.get(q, "Not specified")
    
    return {
        "answers": answers,
        "questionsAnswered": len(answers)
    }

@app.post("/tools/exportFile")
async def export_file(body: dict = Body(...)):
    """Export file to storage (MinIO)"""
    file_path = body.get('filePath')
    doc_id = body.get('docId')
    
    if not file_path and not doc_id:
        raise HTTPException(status_code=400, detail="filePath or docId required")
    
    if not file_path:
        file_path = doc_id
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    minio_url = os.getenv('MINIO_URL', 'http://localhost:9000')
    
    return {
        "filePath": file_path,
        "storageUrl": f"{minio_url}/compliance/{os.path.basename(file_path)}",
        "status": "exported"
    }

@app.post("/tools/emailFile")
async def email_file(body: dict = Body(...)):
    """Send email with attachment via n8n"""
    recipient = body.get('recipient')
    subject = body.get('subject', 'Compliance Document')
    file_path = body.get('filePath')
    body_text = body.get('body', 'Please find attached compliance document.')
    
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient required")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    result = send_email_via_n8n(recipient, subject, body_text, file_path)
    
    return {
        "status": result.get("status", "sent"),
        "recipient": recipient,
        "filePath": file_path,
        "message": result.get("message", "Email sent")
    }

@app.post("/workflow/execute")
async def execute_workflow(body: dict = Body(...)):
    """Execute complete workflow from chat input"""
    text = body.get('text', '')
    user_id = body.get('userId', 1)
    
    if not text:
        raise HTTPException(status_code=400, detail="Text field required")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        intent_result = await detect_intent({"text": text})
        workflow_result = await select_workflow(intent_result)
        
        user_profile = cursor.execute(
            "SELECT * FROM UserProfile WHERE id = ?", (user_id,)
        ).fetchone()
        
        user_dict = dict(user_profile) if user_profile else {}
        
        field_values = {}
        if intent_result['slots'].get('kWh'):
            emissions = estimate_emissions(intent_result['slots']['kWh'])
            field_values['tCO2e'] = emissions['tCO2e']
            field_values['kWh'] = intent_result['slots']['kWh']
        
        field_values['companyName'] = user_dict.get('name', 'Prime Bakery')
        field_values['postalCode'] = user_dict.get('address', '').split()[-1] if user_dict.get('address') else "24937"
        
        pdf_result = await fill_pdf({
            "formId": workflow_result['neededForms'][0],
            "fieldValues": field_values,
            "formType": workflow_result['neededForms'][0]
        })
        
        compliance_pack = generate_compliance_pack(
            submission_id=1,
            intent_type=intent_result['intentType'],
            forms_used=workflow_result['neededForms'],
            regulations=workflow_result['regulations']
        )
        
        submission_data = {
            "userId": user_id,
            "intent": intent_result['intentType'],
            "selected_forms": json.dumps(workflow_result['neededForms']),
            "answers": json.dumps(field_values),
            "files": json.dumps([pdf_result['docId'], compliance_pack]),
            "status": "completed",
            "audit_trail": json.dumps({"intent": intent_result, "workflow": workflow_result})
        }
        
        cursor.execute('''
            INSERT INTO Submission (userId, intent, selected_forms, answers, files, status, audit_trail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_data['userId'],
            submission_data['intent'],
            submission_data['selected_forms'],
            submission_data['answers'],
            submission_data['files'],
            submission_data['status'],
            submission_data['audit_trail']
        ))
        
        conn.commit()
        submission_id = cursor.lastrowid
        
        return {
            "submissionId": submission_id,
            "intent": intent_result,
            "workflow": workflow_result,
            "pdfDocument": pdf_result,
            "compliancePack": compliance_pack,
            "status": "completed"
        }
    finally:
        conn.close()

@app.get("/submissions/{submission_id}")
async def get_submission(submission_id: int):
    """Get submission details"""
    conn = get_db()
    cursor = conn.cursor()
    
    submission = cursor.execute(
        "SELECT * FROM Submission WHERE id = ?", (submission_id,)
    ).fetchone()
    
    conn.close()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return dict(submission)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
