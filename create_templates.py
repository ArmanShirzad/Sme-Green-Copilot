#!/usr/bin/env python3
"""
Create simple PDF templates for compliance forms
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

os.makedirs('templates', exist_ok=True)

def create_gdpr_art30_template():
    """Create GDPR Article 30 Record of Processing Activities template"""
    pdf_path = 'templates/gdpr_art30_record.pdf'
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "GDPR Article 30 - Record of Processing Activities")
    y -= 30
    
    c.setFont("Helvetica", 12)
    fields = [
        ("Controller Name:", "name"),
        ("Controller Address:", "address"),
        ("Contact Person:", "contact_person"),
        ("Processing Purposes:", "processing_purposes"),
        ("Categories of Data Subjects:", "data_subjects"),
        ("Categories of Personal Data:", "data_categories"),
        ("Recipients of Personal Data:", "recipients"),
        ("Transfers to Third Countries:", "transfers"),
        ("Retention Period:", "retention_period"),
        ("Security Measures:", "security_measures"),
        ("Legal Basis (Art. 6):", "legal_basis"),
    ]
    
    for label, field in fields:
        if y < 100:
            c.showPage()
            y = height - 50
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, label)
        y -= 15
        
        c.setFont("Helvetica", 9)
        c.drawString(60, y, f"[{field}]")
        y -= 25
    
    c.save()
    print(f"Created: {pdf_path}")

def create_dpia_template():
    """Create DPIA (GDPR Article 35) template"""
    pdf_path = 'templates/gdpr_dpia_template.pdf'
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Data Protection Impact Assessment (DPIA)")
    c.drawString(50, y - 20, "GDPR Article 35")
    y -= 40
    
    c.setFont("Helvetica", 12)
    sections = [
        ("1. Description of Processing:", "processing_description"),
        ("2. Necessity and Proportionality:", "necessity"),
        ("3. Risk Assessment:", "risk_assessment"),
        ("4. Measures to Address Risks:", "mitigation_measures"),
        ("5. Consultation:", "consultation"),
    ]
    
    for section, field in sections:
        if y < 100:
            c.showPage()
            y = height - 50
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, section)
        y -= 20
        
        c.setFont("Helvetica", 9)
        c.drawString(60, y, f"[{field}]")
        y -= 30
    
    c.save()
    print(f"Created: {pdf_path}")

def create_ai_act_risk_template():
    """Create EU AI Act Risk Classification Worksheet"""
    pdf_path = 'templates/ai_act_risk_worksheet.pdf'
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "EU AI Act - Risk Classification Worksheet")
    y -= 30
    
    c.setFont("Helvetica", 12)
    fields = [
        ("AI System Description:", "system_description"),
        ("Intended Purpose:", "intended_purpose"),
        ("Risk Level:", "risk_level"),
        ("Annex III High-Risk Category:", "annex_iii_category"),
        ("Compliance Requirements:", "compliance_requirements"),
        ("System Card Required:", "system_card_required"),
        ("Transparency Log Required:", "transparency_log"),
    ]
    
    for label, field in fields:
        if y < 100:
            c.showPage()
            y = height - 50
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, label)
        y -= 15
        
        c.setFont("Helvetica", 9)
        c.drawString(60, y, f"[{field}]")
        y -= 25
    
    c.save()
    print(f"Created: {pdf_path}")

def create_vsme_snapshot_template():
    """Create VSME CSRD snapshot template (simplified)"""
    pdf_path = 'templates/vsme_snapshot.pdf'
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "VSME Standard - Climate Snapshot")
    c.drawString(50, y - 20, "CSRD ESRS E1 (SME-friendly)")
    y -= 40
    
    c.setFont("Helvetica", 12)
    fields = [
        ("Company Name:", "company_name"),
        ("Reporting Period:", "reporting_period"),
        ("Energy Consumption (kWh):", "energy_kwh"),
        ("Scope 2 Emissions (tCO2e):", "scope2_emissions"),
        ("Methodology:", "methodology"),
        ("Reduction Actions:", "reduction_actions"),
    ]
    
    for label, field in fields:
        if y < 100:
            c.showPage()
            y = height - 50
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, label)
        y -= 15
        
        c.setFont("Helvetica", 9)
        c.drawString(60, y, f"[{field}]")
        y -= 25
    
    c.save()
    print(f"Created: {pdf_path}")

if __name__ == "__main__":
    print("Creating PDF templates...")
    create_gdpr_art30_template()
    create_dpia_template()
    create_ai_act_risk_template()
    create_vsme_snapshot_template()
    print("Done!")

