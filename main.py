"""
Green SME Compliance Co-Pilot - Main FastAPI Application
Core endpoints for intent detection, workflow orchestration, and compliance automation
"""

from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import models
from models import (
    DetectIntentRequest, DetectIntentResponse,
    SelectWorkflowRequest, SelectWorkflowResponse,
    ParseFormRequest, ParseFormResponse,
    MapFieldsRequest, MapFieldsResponse,
    CollectAnswersRequest, CollectAnswersResponse,
    EstimateEmissionsRequest, EstimateEmissionsResponse,
    FillPdfRequest, FillPdfResponse,
    ExportFileRequest, ExportFileResponse,
    EmailFileRequest, EmailFileResponse,
    GenerateCompliancePackRequest, GenerateCompliancePackResponse,
    WeatherInsightRequest, WeatherInsightResponse,
    LoadShiftRecommendationRequest, LoadShiftRecommendationResponse,
    IntentType
)

# Import utilities (to be created)
from utils import (
    load_embedding_model,
    load_faiss_index,
    detect_intent_with_llm,
    get_user_profile,
    get_workflow_recipe,
    calculate_emissions,
    get_weather_data,
    generate_load_shift_recommendations,
    send_email_via_n8n,
    upload_to_storage,
    add_audit_log
)

from pdf_processor import (
    parse_pdf_form,
    fill_pdf_template,
    generate_compliance_pdf
)


# Global state for models
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize models and resources on startup"""
    print("Initializing Green SME Compliance Co-Pilot...")
    
    # Load ML models
    try:
        app_state['embed_model'] = load_embedding_model()
        app_state['faiss_index'] = load_faiss_index()
        print("ML models loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load ML models: {e}")
        app_state['embed_model'] = None
        app_state['faiss_index'] = None
    
    # Check database
    db_path = os.getenv('DB_PATH', 'db.sqlite')
    if not os.path.exists(db_path):
        print(f"Warning: Database not found at {db_path}. Run db_init.py first.")
    
    # Create output directories
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    print("Application startup complete")
    
    yield
    
    print("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Green SME Compliance Co-Pilot",
    description="AI agent for automating ESG audits and CSRD/GDPR filings",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Green SME Compliance Co-Pilot",
        "version": "0.1.0",
        "models_loaded": app_state.get('embed_model') is not None
    }


@app.post("/tools/detectIntent", response_model=DetectIntentResponse)
async def detect_intent(request: DetectIntentRequest):
    """
    Detect user intent from natural language input
    Extracts intent type and entities/slots
    """
    try:
        result = detect_intent_with_llm(
            text=request.text,
            context=request.context,
            model=app_state.get('embed_model')
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent detection failed: {str(e)}")


@app.post("/tools/selectWorkflow", response_model=SelectWorkflowResponse)
async def select_workflow(request: SelectWorkflowRequest):
    """
    Select appropriate workflow recipe based on intent
    Returns forms needed and any missing information
    """
    try:
        recipe = get_workflow_recipe(
            intent_type=request.intentType,
            slots=request.slots
        )
        
        # Check for missing required information
        questions = []
        if request.intentType == IntentType.ENERGY_AUDIT_FOR_CSRD:
            if 'kWh' not in request.slots:
                questions.append("What is your total energy consumption (kWh) for the last month?")
            if 'city' not in request.slots:
                questions.append("What city are you located in?")
        
        return SelectWorkflowResponse(
            recipeId=recipe['id'],
            neededForms=recipe['forms'],
            questions=questions,
            estimatedTime=recipe.get('estimated_time', '15-20 minutes')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow selection failed: {str(e)}")


@app.post("/tools/parseForm", response_model=ParseFormResponse)
async def parse_form(request: ParseFormRequest):
    """
    Parse PDF form using OCR
    Extract field labels and structure
    """
    try:
        if not os.path.exists(request.pdfPath):
            raise HTTPException(status_code=404, detail=f"PDF not found: {request.pdfPath}")
        
        result = parse_pdf_form(request.pdfPath, request.formId)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Form parsing failed: {str(e)}")


@app.post("/tools/mapFields", response_model=MapFieldsResponse)
async def map_fields(request: MapFieldsRequest):
    """
    Map form fields to user data using semantic similarity
    Uses FAISS for efficient vector search
    """
    try:
        embed_model = app_state.get('embed_model')
        faiss_index = app_state.get('faiss_index')
        
        if embed_model is None:
            # Fallback to rule-based mapping
            field_values = {}
            for label in request.labels:
                label_lower = label.lower()
                if 'name' in label_lower or 'company' in label_lower:
                    field_values[label] = request.userProfile.get('name')
                elif 'address' in label_lower:
                    field_values[label] = request.userProfile.get('address')
                elif 'city' in label_lower:
                    field_values[label] = request.userProfile.get('city')
                elif 'postal' in label_lower or 'zip' in label_lower:
                    field_values[label] = request.userProfile.get('postal_code')
                elif 'email' in label_lower:
                    field_values[label] = request.userProfile.get('email')
                elif 'kwh' in label_lower or 'energy' in label_lower:
                    field_values[label] = request.slots.get('kWh')
                elif 'emission' in label_lower or 'co2' in label_lower:
                    field_values[label] = request.slots.get('tCO2e')
            
            return MapFieldsResponse(fieldValues=field_values, lowConfidence=[])
        
        # TODO: Implement semantic mapping with embeddings
        # For now, use rule-based
        field_values = {}
        low_confidence = []
        
        for label in request.labels:
            # Simplified mapping logic
            mapped_value = None
            confidence = 1.0
            
            # Try direct keyword matching
            if any(kw in label.lower() for kw in ['name', 'company', 'organization']):
                mapped_value = request.userProfile.get('name')
            elif 'address' in label.lower():
                mapped_value = request.userProfile.get('address')
            elif 'city' in label.lower():
                mapped_value = request.userProfile.get('city')
            
            if mapped_value:
                field_values[label] = mapped_value
                if confidence < 0.7:
                    low_confidence.append(label)
        
        return MapFieldsResponse(
            fieldValues=field_values,
            lowConfidence=low_confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Field mapping failed: {str(e)}")


@app.post("/tools/collectAnswers", response_model=CollectAnswersResponse)
async def collect_answers(request: CollectAnswersRequest):
    """
    Collect missing answers from user
    Returns collected responses
    """
    # In real implementation, this would interact with chat or send email
    return CollectAnswersResponse(
        answers={},
        status="pending_user_input"
    )


# ============================================================================
# ESG & COMPLIANCE ENDPOINTS
# ============================================================================

@app.post("/tools/estimateEmissions", response_model=EstimateEmissionsResponse)
async def estimate_emissions(request: EstimateEmissionsRequest):
    """
    Calculate CO2 emissions from energy consumption
    Uses country-specific grid factors
    """
    try:
        result = calculate_emissions(
            kwh=request.kWh,
            grid_factor=request.gridFactor,
            include_scope3=request.includeScope3
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emissions calculation failed: {str(e)}")


@app.post("/tools/getWeatherInsight", response_model=WeatherInsightResponse)
async def get_weather_insight(request: WeatherInsightRequest):
    """
    Get weather data for solar potential analysis
    """
    try:
        result = get_weather_data(request.city, request.country)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {str(e)}")


@app.post("/tools/suggestLoadShift", response_model=LoadShiftRecommendationResponse)
async def suggest_load_shift(request: LoadShiftRecommendationRequest):
    """
    Generate load-shifting recommendations based on energy profile
    """
    try:
        result = generate_load_shift_recommendations(
            kwh_profile=request.kWhProfile,
            weather_hint=request.weatherHint
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load shift calculation failed: {str(e)}")


# ============================================================================
# DOCUMENT GENERATION & EXPORT ENDPOINTS
# ============================================================================

@app.post("/tools/fillPdf", response_model=FillPdfResponse)
async def fill_pdf(request: FillPdfRequest):
    """
    Fill PDF template with provided values
    """
    try:
        output_path = fill_pdf_template(
            form_id=request.formId,
            field_values=request.fieldValues,
            template_path=request.templatePath
        )
        
        return FillPdfResponse(
            docId=os.path.basename(output_path),
            filePath=output_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF filling failed: {str(e)}")


@app.post("/tools/generateCompliancePack", response_model=GenerateCompliancePackResponse)
async def generate_compliance_pack(request: GenerateCompliancePackRequest):
    """
    Generate complete compliance documentation pack
    Includes system card for EU AI Act
    """
    try:
        db_path = os.getenv('DB_PATH', 'db.sqlite')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get submission details
        cursor.execute(
            "SELECT * FROM Submission WHERE id = ?",
            (request.submissionId,)
        )
        submission = cursor.fetchone()
        conn.close()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Generate compliance pack PDF
        output_path = generate_compliance_pdf(
            submission_id=request.submissionId,
            regulations=request.regulations
        )
        
        return GenerateCompliancePackResponse(
            packId=f"pack_{request.submissionId}",
            filePath=output_path,
            regulations=[{"name": reg, "status": "compliant"} for reg in request.regulations],
            systemCard=output_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance pack generation failed: {str(e)}")


@app.post("/tools/exportFile", response_model=ExportFileResponse)
async def export_file(request: ExportFileRequest):
    """
    Export generated document to storage
    Returns download URL
    """
    try:
        file_path = f"outputs/{request.docId}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Upload to MinIO or return local path
        storage_url = upload_to_storage(file_path)
        
        return ExportFileResponse(
            downloadUrl=storage_url,
            fileSize=os.path.getsize(file_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File export failed: {str(e)}")


@app.post("/tools/emailFile", response_model=EmailFileResponse)
async def email_file(request: EmailFileRequest):
    """
    Send generated document via email
    Uses n8n webhook for email delivery
    """
    try:
        result = send_email_via_n8n(
            recipient=request.recipient,
            subject=request.subject,
            body=request.body or "Please find attached compliance documents.",
            attachments=[request.docId] + request.attachments
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")


@app.get("/tools/downloadFile/{doc_id}")
async def download_file(doc_id: str):
    """
    Download generated file
    """
    file_path = f"outputs/{doc_id}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=doc_id
    )


# ============================================================================
# ADMIN & UTILITY ENDPOINTS
# ============================================================================

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    """Get user profile"""
    try:
        profile = get_user_profile(user_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"User not found: {str(e)}")


@app.get("/submissions/{user_id}")
async def get_submissions(user_id: int):
    """Get user's submission history"""
    try:
        db_path = os.getenv('DB_PATH', 'db.sqlite')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM Submission WHERE userId = ? ORDER BY created_at DESC",
            (user_id,)
        )
        
        columns = [desc[0] for desc in cursor.description]
        submissions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return submissions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch submissions: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('APP_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
