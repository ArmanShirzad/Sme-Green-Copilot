import os
import requests
import random
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import yaml
from datetime import datetime

load_dotenv()

def get_weather(city):
    """Fetch weather data for a city using OpenWeather API"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key or api_key == 'your_openweather_api_key_here':
        return {"sunHours": 5.0, "temperature": 15, "note": "Mock data - API key not configured"}
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            sunrise = data.get('sys', {}).get('sunrise', 0)
            sunset = data.get('sys', {}).get('sunset', 0)
            sun_hours = (sunset - sunrise) / 3600 if sunset > sunrise else 5.0
            return {
                "sunHours": round(sun_hours, 1),
                "temperature": data.get('main', {}).get('temp', 15),
                "humidity": data.get('main', {}).get('humidity', 50),
                "note": "Real data from OpenWeather"
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    
    return {"sunHours": 5.0, "temperature": 15, "note": "Fallback mock data"}

def suggest_load_shift(kwh_profile, weather_hint):
    """Suggest load shifting based on kWh profile and weather"""
    sun_hours = weather_hint.get('sunHours', 5.0)
    suggestions = []
    
    if sun_hours > 5:
        suggestions.append("Shift dishwasher to 12-14 for PV savings")
        suggestions.append("Preheat ovens during peak solar hours (11-15)")
    
    if kwh_profile.get('peak_hours', []):
        suggestions.append("Consider shifting high-consumption activities to off-peak hours")
    
    if not suggestions:
        suggestions.append("No shift recommended based on current profile")
    
    return suggestions

def load_compliance_matrix():
    """Load compliance matrix from YAML"""
    matrix_path = 'config/compliance_matrix.yaml'
    if os.path.exists(matrix_path):
        with open(matrix_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def generate_compliance_pack(submission_id, intent_type, forms_used, regulations):
    """Generate compliance pack PDF with system card and audit trail"""
    pack_path = f"compliance_pack_{submission_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(pack_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Compliance Pack - System Card")
    y -= 30
    
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Submission ID: {submission_id}")
    y -= 20
    c.drawString(50, y, f"Intent Type: {intent_type}")
    y -= 20
    c.drawString(50, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Forms Processed:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for form in forms_used:
        c.drawString(70, y, f"- {form}")
        y -= 15
    
    y -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Regulations Addressed:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for reg in regulations:
        c.drawString(70, y, f"- {reg}")
        y -= 15
    
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "GDPR Art.30 Compliance:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    gdpr_text = [
        "Controller details: Automated via semantic mapping",
        "Processing purposes: Extracted from form fields",
        "Data categories: Classified per GDPR Art.30 requirements",
        "Recipients: Mapped from form structure",
        "Retention periods: Inferred from business context",
        "Security measures: Documented in audit trail"
    ]
    for line in gdpr_text:
        c.drawString(70, y, line)
        y -= 15
    
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "EU AI Act Transparency:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    ai_act_text = [
        "AI System: Green SME Compliance Co-Pilot",
        "Purpose: Automated form filling and compliance checking",
        "Risk Level: Low (assistance tool, human-in-the-loop)",
        "Data Processing: Semantic embeddings, no training data stored",
        "Transparency: Full audit trail maintained",
        "Human Oversight: Required for all submissions"
    ]
    for line in ai_act_text:
        c.drawString(70, y, line)
        y -= 15
    
    c.save()
    return pack_path

def estimate_emissions(kwh, grid_factor=None, country='DE'):
    """Estimate CO2 emissions from kWh consumption"""
    grid_factors = {
        'DE': 0.42,
        'FR': 0.05,
        'ES': 0.25,
        'IT': 0.35,
        'UK': 0.25
    }
    
    factor = grid_factor or grid_factors.get(country, 0.42)
    tco2e = (kwh * factor) / 1000
    
    return {
        "tCO2e": round(tco2e, 2),
        "kWh": kwh,
        "gridFactor": factor,
        "country": country,
        "note": f"Estimated with {country} grid factor ({factor} kg CO2/kWh)"
    }

def send_email_via_n8n(recipient, subject, body, attachment_path=None):
    """Send email via n8n webhook"""
    webhook_url = os.getenv('N8N_WEBHOOK_URL')
    if not webhook_url or webhook_url == 'http://localhost:5678/webhook/compliance-email':
        print(f"Mock email: To {recipient}, Subject: {subject}")
        return {"status": "mock", "message": "Email would be sent via n8n"}
    
    payload = {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "attachment": attachment_path
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return {"status": "sent", "response": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
