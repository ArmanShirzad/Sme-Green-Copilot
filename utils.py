import os
import requests
import yaml
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def get_weather(city):
    """Fetch weather data for energy optimization suggestions."""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key or api_key == 'your_openweather_api_key_here':
        return {"sunHours": 5.0, "temperature": 15.0, "note": "Mock data - API key not configured"}
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Estimate sun hours from cloud coverage
            clouds = data.get('clouds', {}).get('all', 50)
            sun_hours = max(0, 12 - (clouds / 10))
            return {
                "sunHours": round(sun_hours, 1),
                "temperature": data.get('main', {}).get('temp', 15),
                "clouds": clouds,
                "note": "Real data from OpenWeather"
            }
    except Exception as e:
        pass
    
    return {"sunHours": 5.0, "temperature": 15.0, "note": "Offline mock data"}

def suggest_load_shift(kwh_profile, weather_hint):
    """Suggest load shifting based on energy profile and weather."""
    suggestions = []
    sun_hours = weather_hint.get('sunHours', 5.0)
    
    if sun_hours > 5:
        suggestions.append("Shift dishwasher to 12-14 for PV savings")
        suggestions.append("Consider running high-load appliances during peak solar hours")
    
    if kwh_profile and kwh_profile.get('peak_hours'):
        suggestions.append(f"Peak demand detected at {kwh_profile['peak_hours']} - consider shifting")
    
    if not suggestions:
        suggestions.append("No load shift recommended based on current profile")
    
    return suggestions

def calculate_emissions(kwh, grid_factor=0.42, country="DE"):
    """Calculate CO2 emissions from energy consumption.
    
    Args:
        kwh: Energy consumption in kWh
        grid_factor: Grid emission factor in kg CO2/kWh (default 0.42 for Germany)
        country: Country code for default grid factors
    
    Returns:
        dict with tCO2e and metadata
    """
    country_factors = {
        "DE": 0.42,  # Germany
        "FR": 0.056,  # France (nuclear-heavy)
        "PL": 0.724,  # Poland (coal-heavy)
        "ES": 0.25,   # Spain
    }
    
    if country in country_factors:
        grid_factor = country_factors[country]
    
    tco2e = (kwh * grid_factor) / 1000  # Convert kg to tonnes
    return {
        "tCO2e": round(tco2e, 3),
        "kWh": kwh,
        "gridFactor": grid_factor,
        "country": country,
        "note": f"Estimated with {country} grid factor"
    }

def load_recipes():
    """Load recipe configurations from YAML."""
    try:
        with open('config/recipes.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return {"recipes": {}}

def load_regulations():
    """Load regulatory mappings from YAML."""
    try:
        with open('config/regulations.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading regulations: {e}")
        return {"regulations": {}}

def generate_compliance_pack(submission_id, recipe_id, regulations_list):
    """Generate compliance pack PDF with regulatory mappings."""
    db_path = os.getenv('DB_PATH', 'db.sqlite')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get submission data
    c.execute("SELECT * FROM Submission WHERE id = ?", (submission_id,))
    submission = c.fetchone()
    
    if not submission:
        conn.close()
        return None
    
    # Load regulations
    regs = load_regulations()
    
    # Generate PDF
    pdf_path = f"outputs/compliance_pack_{submission_id}.pdf"
    c_pdf = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c_pdf.setFont("Helvetica-Bold", 16)
    c_pdf.drawString(50, y, "Compliance Pack")
    y -= 30
    
    c_pdf.setFont("Helvetica", 12)
    c_pdf.drawString(50, y, f"Submission ID: {submission_id}")
    y -= 20
    c_pdf.drawString(50, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30
    
    # Add regulatory sections
    for reg_name in regulations_list:
        reg_data = regs.get('regulations', {}).get(reg_name, {})
        if reg_data:
            c_pdf.setFont("Helvetica-Bold", 14)
            c_pdf.drawString(50, y, f"Regulation: {reg_name}")
            y -= 20
            
            c_pdf.setFont("Helvetica", 10)
            if 'articles' in reg_data:
                for article in reg_data['articles']:
                    c_pdf.drawString(70, y, f"{article.get('id', '')}: {article.get('name', '')}")
                    y -= 15
                    if y < 50:
                        c_pdf.showPage()
                        y = height - 50
            
            y -= 10
    
    # Add compliance pack sections
    recipe_data = load_recipes()
    recipe = recipe_data.get('recipes', {}).get(recipe_id, {})
    if recipe and 'regulations' in recipe:
        c_pdf.setFont("Helvetica-Bold", 12)
        c_pdf.drawString(50, y, "Compliance Sections:")
        y -= 20
        c_pdf.setFont("Helvetica", 10)
        for section in recipe.get('regulations', []):
            c_pdf.drawString(70, y, f"- {section}")
            y -= 15
            if y < 50:
                c_pdf.showPage()
                y = height - 50
    
    c_pdf.save()
    
    # Store in database
    c.execute('''
        INSERT INTO CompliancePack (submission_id, pack_type, file_path, regulations)
        VALUES (?, ?, ?, ?)
    ''', (submission_id, recipe_id, pdf_path, ','.join(regulations_list)))
    conn.commit()
    conn.close()
    
    return pdf_path

def classify_ai_risk(ai_system_description):
    """Classify AI system risk level per EU AI Act."""
    high_risk_keywords = [
        "biometric", "identification", "recognition",
        "critical infrastructure", "infrastructure",
        "education", "training", "assessment",
        "employment", "recruitment", "hiring",
        "essential services", "credit", "insurance",
        "law enforcement", "criminal", "justice",
        "migration", "border", "asylum"
    ]
    
    description_lower = ai_system_description.lower()
    matches = [kw for kw in high_risk_keywords if kw in description_lower]
    
    if matches:
        return {
            "risk_level": "high",
            "reason": f"Matches high-risk categories: {', '.join(matches[:3])}",
            "requires_annex_iii": True,
            "compliance_requirements": ["Risk assessment", "System card", "Transparency log"]
        }
    else:
        return {
            "risk_level": "low",
            "reason": "No high-risk indicators found",
            "requires_annex_iii": False,
            "compliance_requirements": ["Basic transparency"]
        }
