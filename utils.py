"""
Utility Functions for Green SME Compliance Co-Pilot
ESG calculations, weather integration, LLM operations, and storage
"""

import os
import json
import sqlite3
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import yaml

from models import (
    DetectIntentResponse, IntentType,
    EstimateEmissionsResponse,
    WeatherInsightResponse,
    LoadShiftRecommendationResponse,
    EmailFileResponse
)


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_embedding_model():
    """Load sentence transformer model for embeddings"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('intfloat/multilingual-e5-large')
        print("Loaded embedding model: intfloat/multilingual-e5-large")
        return model
    except Exception as e:
        print(f"Warning: Could not load embedding model: {e}")
        return None


def load_faiss_index():
    """Load or initialize FAISS index for vector search"""
    try:
        import faiss
        dimension = 1024  # multilingual-e5-large dimension
        index = faiss.IndexFlatL2(dimension)
        print(f"Initialized FAISS index with dimension {dimension}")
        return index
    except Exception as e:
        print(f"Warning: Could not initialize FAISS: {e}")
        return None


# ============================================================================
# INTENT DETECTION & NLP
# ============================================================================

def detect_intent_with_llm(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    model: Any = None
) -> DetectIntentResponse:
    """
    Detect intent from user text using pattern matching and LLM
    Returns intent type, extracted slots, and confidence
    """
    text_lower = text.lower()
    
    # Pattern-based intent detection (fallback for MVP)
    slots = {}
    intent_type = IntentType.GENERAL_COMPLIANCE
    confidence = 0.5
    
    # Energy audit patterns
    if any(kw in text_lower for kw in ['energy', 'audit', 'consumption', 'kwh', 'csrd']):
        intent_type = IntentType.ENERGY_AUDIT_FOR_CSRD
        confidence = 0.85
        
        # Extract energy value
        import re
        kwh_match = re.search(r'(\d+[\.,]?\d*)\s*(kwh|kilowatt)', text_lower)
        if kwh_match:
            slots['kWh'] = float(kwh_match.group(1).replace(',', '.'))
        
        # Extract city
        city_match = re.search(r'in\s+(\w+)|from\s+(\w+)|location[:\s]+(\w+)', text_lower)
        if city_match:
            slots['city'] = city_match.group(1) or city_match.group(2) or city_match.group(3)
    
    # GDPR patterns
    elif any(kw in text_lower for kw in ['gdpr', 'article 30', 'art. 30', 'data protection', 'record of processing']):
        intent_type = IntentType.GDPR_ART30_EXPORT
        confidence = 0.9
    
    # AI Act patterns
    elif any(kw in text_lower for kw in ['ai act', 'ai risk', 'artificial intelligence act', 'high-risk ai']):
        intent_type = IntentType.EU_AI_ACT_RISK
        confidence = 0.88
    
    # Energy optimization patterns
    elif any(kw in text_lower for kw in ['optimize', 'reduce cost', 'save energy', 'load shift']):
        intent_type = IntentType.ENERGY_OPTIMIZATION
        confidence = 0.82
    
    return DetectIntentResponse(
        intentType=intent_type,
        slots=slots,
        confidence=confidence,
        entities=[{"type": k, "value": v} for k, v in slots.items()]
    )


# ============================================================================
# WORKFLOW & RECIPES
# ============================================================================

def get_workflow_recipe(intent_type: IntentType, slots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get workflow recipe configuration for given intent
    """
    recipes = {
        IntentType.ENERGY_AUDIT_FOR_CSRD: {
            "id": "csrd_energy_audit",
            "name": "CSRD Energy Audit & VSME Snapshot",
            "forms": ["vsme_snapshot", "disclosure_letter"],
            "steps": [
                "collect_energy_data",
                "calculate_emissions",
                "get_weather_insights",
                "suggest_load_shift",
                "fill_vsme_form",
                "generate_compliance_pack",
                "export_and_email"
            ],
            "estimated_time": "15-20 minutes",
            "regulations": ["CSRD", "VSME", "ESRS_E1"]
        },
        IntentType.GDPR_ART30_EXPORT: {
            "id": "gdpr_art30_export",
            "name": "GDPR Article 30 Record Export",
            "forms": ["gdpr_art30"],
            "steps": [
                "collect_processing_details",
                "map_legal_bases",
                "fill_art30_form",
                "generate_compliance_pack",
                "export_and_email"
            ],
            "estimated_time": "10-15 minutes",
            "regulations": ["GDPR", "Art30"]
        },
        IntentType.EU_AI_ACT_RISK: {
            "id": "eu_ai_act_risk",
            "name": "EU AI Act Risk Assessment",
            "forms": ["eu_ai_act_risk"],
            "steps": [
                "collect_system_details",
                "classify_risk_category",
                "check_prohibited_practices",
                "fill_risk_form",
                "generate_system_card",
                "export_and_email"
            ],
            "estimated_time": "20-25 minutes",
            "regulations": ["EU_AI_Act", "Annex_III"]
        },
        IntentType.ENERGY_OPTIMIZATION: {
            "id": "energy_optimization",
            "name": "Energy Optimization Recommendations",
            "forms": [],
            "steps": [
                "analyze_energy_profile",
                "get_weather_forecast",
                "suggest_load_shifts",
                "calculate_savings",
                "generate_report"
            ],
            "estimated_time": "5-10 minutes",
            "regulations": []
        }
    }
    
    return recipes.get(intent_type, recipes[IntentType.GENERAL_COMPLIANCE])


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_user_profile(user_id: int) -> Dict[str, Any]:
    """Fetch user profile from database"""
    db_path = os.getenv('DB_PATH', 'db.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM UserProfile WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise ValueError(f"User {user_id} not found")
    
    columns = [desc[0] for desc in cursor.description]
    profile = dict(zip(columns, row))
    
    # Parse JSON fields
    if profile.get('business_facts'):
        try:
            profile['business_facts'] = json.loads(profile['business_facts'])
        except:
            pass
    
    conn.close()
    return profile


def add_audit_log(
    submission_id: int,
    regulation: str,
    action: str,
    status: str = "completed",
    evidence: Optional[str] = None
):
    """Add entry to compliance audit log"""
    db_path = os.getenv('DB_PATH', 'db.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO ComplianceLog (submission_id, regulation, action, status, evidence)
        VALUES (?, ?, ?, ?, ?)
    """, (submission_id, regulation, action, status, evidence or ""))
    
    conn.commit()
    conn.close()


# ============================================================================
# ESG CALCULATIONS
# ============================================================================

def calculate_emissions(
    kwh: float,
    grid_factor: float = 0.42,
    include_scope3: bool = False
) -> EstimateEmissionsResponse:
    """
    Calculate CO2 emissions from energy consumption
    Default grid factor: 0.42 kg CO2/kWh (Germany average)
    """
    scope2 = kwh * grid_factor / 1000  # Convert to tonnes
    
    # Simplified Scope 3 estimation (upstream emissions)
    scope3 = None
    if include_scope3:
        scope3 = scope2 * 0.15  # ~15% additional for upstream
    
    total = scope2 + (scope3 or 0)
    
    breakdown = {
        "electricity_scope2": round(scope2, 3),
    }
    
    if scope3:
        breakdown["upstream_scope3"] = round(scope3, 3)
    
    note = f"Calculated using grid emission factor {grid_factor} kg CO2/kWh"
    if grid_factor == 0.42:
        note += " (Germany average)"
    
    return EstimateEmissionsResponse(
        tCO2e=round(total, 3),
        scope2=round(scope2, 3),
        scope3=round(scope3, 3) if scope3 else None,
        note=note,
        breakdown=breakdown
    )


# ============================================================================
# WEATHER & INSIGHTS
# ============================================================================

def get_weather_data(city: str, country: str = "DE") -> WeatherInsightResponse:
    """
    Fetch weather data from OpenWeatherMap API
    Calculate solar potential (sun hours)
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key or api_key == 'your_openweather_api_key_here':
        # Return mock data for development
        return WeatherInsightResponse(
            sunHours=5.2,
            temperature=12.5,
            recommendation="Moderate solar potential. Consider load shifting to midday hours."
        )
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant data
        temp = data.get('main', {}).get('temp', 15)
        clouds = data.get('clouds', {}).get('all', 50)
        
        # Estimate sun hours based on cloud cover (simplified)
        max_daylight = 12  # hours
        sun_hours = max_daylight * (1 - clouds / 100)
        
        recommendation = ""
        if sun_hours > 6:
            recommendation = "High solar potential. Excellent for PV utilization and load shifting."
        elif sun_hours > 4:
            recommendation = "Moderate solar potential. Consider load shifting to midday hours."
        else:
            recommendation = "Low solar potential today. Grid consumption recommended."
        
        return WeatherInsightResponse(
            sunHours=round(sun_hours, 1),
            temperature=round(temp, 1),
            recommendation=recommendation
        )
    
    except Exception as e:
        print(f"Weather API error: {e}")
        # Fallback to offline estimation
        return WeatherInsightResponse(
            sunHours=5.0,
            temperature=12.0,
            recommendation="Weather data unavailable. Using average estimates."
        )


def generate_load_shift_recommendations(
    kwh_profile: Dict[str, float],
    weather_hint: Optional[Dict[str, Any]] = None
) -> LoadShiftRecommendationResponse:
    """
    Generate load-shifting recommendations based on energy profile and weather
    """
    recommendations = []
    potential_savings = 0.0
    best_time_slots = []
    
    # Analyze if weather is favorable for solar
    sun_hours = weather_hint.get('sunHours', 5.0) if weather_hint else 5.0
    
    if sun_hours > 5:
        recommendations.append(
            "High solar radiation expected. Shift heavy loads (dishwasher, laundry, baking) to 11:00-15:00 for maximum PV self-consumption."
        )
        best_time_slots.append("11:00-15:00")
        potential_savings = 0.15  # 15% savings estimate
    elif sun_hours > 3:
        recommendations.append(
            "Moderate solar potential. Consider shifting flexible loads to midday (12:00-14:00)."
        )
        best_time_slots.append("12:00-14:00")
        potential_savings = 0.08
    else:
        recommendations.append(
            "Low solar potential. Use grid off-peak hours (22:00-06:00) for cost savings if applicable."
        )
        best_time_slots.append("22:00-06:00")
        potential_savings = 0.05
    
    # Add general recommendations
    recommendations.append(
        "Install smart plugs to automate load shifting based on real-time solar generation."
    )
    recommendations.append(
        "Monitor energy consumption with smart meters for data-driven optimization."
    )
    
    return LoadShiftRecommendationResponse(
        recommendations=recommendations,
        potentialSavings=potential_savings,
        bestTimeSlots=best_time_slots
    )


# ============================================================================
# STORAGE & FILE MANAGEMENT
# ============================================================================

def upload_to_storage(file_path: str) -> str:
    """
    Upload file to MinIO storage
    Returns public URL or local path if MinIO unavailable
    """
    minio_url = os.getenv('MINIO_URL')
    
    if not minio_url or minio_url == 'http://localhost:9000':
        # Return local file path for development
        return f"/tools/downloadFile/{os.path.basename(file_path)}"
    
    try:
        from minio import Minio
        
        client = Minio(
            minio_url.replace('http://', ''),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            secure=False
        )
        
        bucket_name = os.getenv('MINIO_BUCKET', 'compliance-docs')
        
        # Create bucket if not exists
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        
        # Upload file
        object_name = os.path.basename(file_path)
        client.fput_object(bucket_name, object_name, file_path)
        
        return f"{minio_url}/{bucket_name}/{object_name}"
    
    except Exception as e:
        print(f"MinIO upload failed: {e}")
        return f"/tools/downloadFile/{os.path.basename(file_path)}"


# ============================================================================
# EMAIL & NOTIFICATIONS
# ============================================================================

def send_email_via_n8n(
    recipient: str,
    subject: str,
    body: str,
    attachments: List[str] = None
) -> EmailFileResponse:
    """
    Send email via n8n webhook
    """
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    
    if not webhook_url or 'localhost' in webhook_url:
        # Mock response for development
        print(f"[MOCK EMAIL] To: {recipient}, Subject: {subject}")
        return EmailFileResponse(
            status="sent_mock",
            messageId=f"mock_{datetime.now().timestamp()}",
            sentAt=datetime.now()
        )
    
    try:
        payload = {
            "to": recipient,
            "subject": subject,
            "body": body,
            "attachments": attachments or []
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        return EmailFileResponse(
            status="sent",
            messageId=result.get('messageId'),
            sentAt=datetime.now()
        )
    
    except Exception as e:
        print(f"Email sending failed: {e}")
        return EmailFileResponse(
            status="failed",
            messageId=None,
            sentAt=datetime.now()
        )


# ============================================================================
# COMPLIANCE MATRIX
# ============================================================================

def load_compliance_matrix() -> Dict[str, Any]:
    """
    Load compliance matrix from YAML
    Maps features to regulatory requirements
    """
    matrix_path = "config/compliance_matrix.yaml"
    
    if not os.path.exists(matrix_path):
        # Return default matrix
        return {
            "regulations": {
                "GDPR_Art30": {
                    "name": "GDPR Article 30",
                    "features": ["user_profile", "data_mapping", "audit_log"],
                    "evidence": ["art30_record.pdf", "audit_trail.json"]
                },
                "CSRD_VSME": {
                    "name": "CSRD Voluntary SME Standard",
                    "features": ["energy_data", "emissions_calc", "vsme_snapshot"],
                    "evidence": ["vsme_report.pdf", "energy_audit.json"]
                },
                "EU_AI_Act": {
                    "name": "EU AI Act",
                    "features": ["system_card", "transparency_log", "risk_assessment"],
                    "evidence": ["system_card.pdf", "transparency_log.json"]
                }
            }
        }
    
    with open(matrix_path, 'r') as f:
        return yaml.safe_load(f)
