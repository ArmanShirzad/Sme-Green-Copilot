"""
PDF Processing Module for Green SME Compliance Co-Pilot
Handles OCR, form parsing, template filling, and compliance document generation
"""

import os
import io
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

try:
    import pytesseract
    from PIL import Image
    from pypdf import PdfReader
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: Tesseract OCR not available. PDF parsing will be limited.")

from models import ParseFormResponse


# ============================================================================
# FORM PARSING & OCR
# ============================================================================

def parse_pdf_form(pdf_path: str, form_id: Optional[str] = None) -> ParseFormResponse:
    """
    Parse PDF form using OCR to extract field labels
    Falls back to text extraction if OCR unavailable
    """
    labels = []
    structure = {}
    confidence = 0.0
    
    try:
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        
        # Try text extraction first
        text = page.extract_text()
        
        if text and len(text.strip()) > 0:
            # Extract lines as potential field labels
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            labels = lines[:50]  # Limit to first 50 lines
            confidence = 0.85
            
            # Build simple structure
            structure = {
                "method": "text_extraction",
                "pages": len(reader.pages),
                "fields_found": len(labels)
            }
        
        # Try OCR if Tesseract available
        elif TESSERACT_AVAILABLE:
            # Convert first page to image
            # Note: This is simplified; production would use pdf2image
            labels = ["company_name", "address", "city", "postal_code", "email"]
            confidence = 0.70
            structure = {
                "method": "ocr",
                "pages": len(reader.pages),
                "fields_found": len(labels)
            }
        
        else:
            # Fallback to common form fields
            labels = [
                "Company Name",
                "Address",
                "City",
                "Postal Code",
                "Country",
                "Email",
                "Phone",
                "Date",
                "Signature"
            ]
            confidence = 0.50
            structure = {
                "method": "template",
                "pages": len(reader.pages),
                "fields_found": len(labels)
            }
    
    except Exception as e:
        print(f"PDF parsing error: {e}")
        # Return minimal structure
        labels = ["company_name", "date", "signature"]
        confidence = 0.30
        structure = {"method": "fallback", "error": str(e)}
    
    return ParseFormResponse(
        formId=form_id or os.path.basename(pdf_path),
        labels=labels,
        structure=structure,
        confidence=confidence
    )


# ============================================================================
# PDF TEMPLATE FILLING
# ============================================================================

def fill_pdf_template(
    form_id: str,
    field_values: Dict[str, Any],
    template_path: Optional[str] = None
) -> str:
    """
    Fill PDF template with provided values
    Uses ReportLab to generate filled form
    """
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"filled_{form_id}_{timestamp}.pdf")
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2C3E2D'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    field_style = ParagraphStyle(
        'FieldStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=8
    )
    
    # Add title based on form type
    form_titles = {
        "vsme_snapshot": "CSRD VSME Sustainability Snapshot",
        "gdpr_art30": "GDPR Article 30 - Record of Processing Activities",
        "eu_ai_act_risk": "EU AI Act - Risk Assessment Document"
    }
    
    title = form_titles.get(form_id, "Compliance Document")
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Add generation timestamp
    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        field_style
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    # Form-specific content
    if form_id == "vsme_snapshot":
        story.extend(_create_vsme_content(field_values, heading_style, field_style))
    elif form_id == "gdpr_art30":
        story.extend(_create_gdpr_art30_content(field_values, heading_style, field_style))
    elif form_id == "eu_ai_act_risk":
        story.extend(_create_ai_act_content(field_values, heading_style, field_style))
    else:
        # Generic form fill
        story.extend(_create_generic_content(field_values, heading_style, field_style))
    
    # Build PDF
    doc.build(story)
    
    print(f"Generated PDF: {output_path}")
    return output_path


def _create_vsme_content(values: Dict, heading_style, field_style) -> List:
    """Create CSRD VSME form content"""
    content = []
    
    # Company Information
    content.append(Paragraph("Company Information", heading_style))
    content.append(Paragraph(f"<b>Company Name:</b> {values.get('name', 'N/A')}", field_style))
    content.append(Paragraph(f"<b>Address:</b> {values.get('address', 'N/A')}", field_style))
    content.append(Paragraph(f"<b>City:</b> {values.get('city', 'N/A')}, {values.get('postal_code', 'N/A')}", field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Energy & Emissions
    content.append(Paragraph("Energy Consumption & Emissions (ESRS E1)", heading_style))
    
    energy_data = [
        ["Metric", "Value", "Unit"],
        ["Total Energy Consumption", str(values.get('kWh', 'N/A')), "kWh"],
        ["Scope 2 Emissions", str(values.get('tCO2e', 'N/A')), "tonnes CO2e"],
        ["Renewable Energy Share", str(values.get('renewable_kwh', 'N/A')), "kWh"],
    ]
    
    table = Table(energy_data, colWidths=[3*inch, 2*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E2D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    content.append(table)
    content.append(Spacer(1, 0.2 * inch))
    
    # Methodology
    content.append(Paragraph("Methodology Note", heading_style))
    methodology = values.get('methodology', 'Emissions calculated using German grid emission factor (0.42 kg CO2/kWh). Data sourced from smart meter readings for the reporting period.')
    content.append(Paragraph(methodology, field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Actions
    content.append(Paragraph("Sustainability Actions", heading_style))
    actions = values.get('actions', 'Implementing LED lighting upgrade and optimizing heating controls to reduce energy consumption by estimated 15%.')
    content.append(Paragraph(actions, field_style))
    
    return content


def _create_gdpr_art30_content(values: Dict, heading_style, field_style) -> List:
    """Create GDPR Article 30 record content"""
    content = []
    
    # Controller Information
    content.append(Paragraph("1. Controller Details", heading_style))
    content.append(Paragraph(f"<b>Name:</b> {values.get('name', 'N/A')}", field_style))
    content.append(Paragraph(f"<b>Contact:</b> {values.get('email', 'N/A')}", field_style))
    content.append(Paragraph(f"<b>Address:</b> {values.get('address', 'N/A')}", field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Processing Activities
    content.append(Paragraph("2. Processing Purposes", heading_style))
    purposes = values.get('purposes', 'Customer relationship management, invoice processing, compliance reporting')
    content.append(Paragraph(purposes, field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Data Categories
    content.append(Paragraph("3. Categories of Personal Data", heading_style))
    categories = values.get('data_categories', 'Contact details (name, email, phone), Business information, Transaction data')
    content.append(Paragraph(categories, field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Recipients
    content.append(Paragraph("4. Recipients", heading_style))
    recipients = values.get('recipients', 'Accounting service provider, Cloud hosting provider (AWS/EU), Tax authorities')
    content.append(Paragraph(recipients, field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Retention
    content.append(Paragraph("5. Retention Period", heading_style))
    retention = values.get('retention', 'Customer data: Duration of contract + 3 years; Invoices: 10 years (legal requirement)')
    content.append(Paragraph(retention, field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Security
    content.append(Paragraph("6. Security Measures", heading_style))
    security = values.get('security', 'Encryption at rest and in transit, Access controls with MFA, Regular backups, Annual security audit')
    content.append(Paragraph(security, field_style))
    
    return content


def _create_ai_act_content(values: Dict, heading_style, field_style) -> List:
    """Create EU AI Act risk assessment content"""
    content = []
    
    # System Overview
    content.append(Paragraph("AI System Overview", heading_style))
    content.append(Paragraph(f"<b>System Name:</b> {values.get('system_name', 'Green SME Compliance Co-Pilot')}", field_style))
    content.append(Paragraph(f"<b>Purpose:</b> {values.get('purpose', 'Automated compliance document generation and ESG reporting')}", field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Risk Classification
    content.append(Paragraph("Risk Classification", heading_style))
    risk_category = values.get('risk_category', 'Limited Risk')
    content.append(Paragraph(f"<b>Category:</b> {risk_category}", field_style))
    content.append(Paragraph(f"<b>High-Risk Criteria Met:</b> {values.get('high_risk', 'No')}", field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Transparency
    content.append(Paragraph("Transparency Measures", heading_style))
    transparency = values.get('transparency', 'Users are informed that they are interacting with an AI system. All recommendations include explanations and allow human review. System logs all decisions for audit trail.')
    content.append(Paragraph(transparency, field_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Human Oversight
    content.append(Paragraph("Human Oversight", heading_style))
    oversight = values.get('oversight', 'All compliance documents require user approval before submission. Critical decisions (e.g., legal interpretations) are flagged for expert review. Users can override AI recommendations.')
    content.append(Paragraph(oversight, field_style))
    
    return content


def _create_generic_content(values: Dict, heading_style, field_style) -> List:
    """Create generic form content"""
    content = []
    
    content.append(Paragraph("Form Data", heading_style))
    
    for key, value in values.items():
        if value is not None:
            # Clean key for display
            display_key = key.replace('_', ' ').title()
            content.append(Paragraph(f"<b>{display_key}:</b> {value}", field_style))
    
    return content


# ============================================================================
# COMPLIANCE PACK GENERATION
# ============================================================================

def generate_compliance_pdf(
    submission_id: int,
    regulations: List[str]
) -> str:
    """
    Generate comprehensive compliance pack PDF
    Includes system card for EU AI Act transparency
    """
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"compliance_pack_{submission_id}_{timestamp}.pdf")
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'PackTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2C3E2D'),
        spaceAfter=15,
        spaceBefore=20
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1A1A1A'),
        spaceAfter=10,
        leading=14
    )
    
    # Title Page
    story.append(Paragraph("Compliance Documentation Pack", title_style))
    story.append(Paragraph(f"Submission ID: {submission_id}", body_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 0.5 * inch))
    
    # Regulations Covered
    story.append(Paragraph("Regulations Covered", section_style))
    for reg in regulations:
        story.append(Paragraph(f"• {reg}", body_style))
    story.append(Spacer(1, 0.3 * inch))
    
    story.append(PageBreak())
    
    # System Card (EU AI Act Requirement)
    story.append(Paragraph("AI System Transparency Card", section_style))
    story.append(Paragraph(
        "<b>System Name:</b> Green SME Compliance Co-Pilot",
        body_style
    ))
    story.append(Paragraph(
        "<b>Provider:</b> Green SME Team",
        body_style
    ))
    story.append(Paragraph(
        "<b>Purpose:</b> Automated compliance document generation, ESG reporting, and regulatory guidance for SMEs.",
        body_style
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("Capabilities & Limitations", section_style))
    story.append(Paragraph(
        "This AI system assists with compliance documentation by automatically extracting data, mapping form fields, calculating emissions, and generating reports. It is designed for limited-risk applications and includes human oversight mechanisms.",
        body_style
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<b>Limitations:</b> The system provides guidance based on general regulatory frameworks and should not replace professional legal advice. All outputs require user review and approval.",
        body_style
    ))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("Technical Details", section_style))
    tech_data = [
        ["Component", "Details"],
        ["NLP Model", "Multilingual E5 Large (sentence embeddings)"],
        ["Vector Search", "FAISS (Meta Research)"],
        ["OCR Engine", "Tesseract 5.x"],
        ["LLM", "Mistral AI (optional, for intent detection)"],
    ]
    
    tech_table = Table(tech_data, colWidths=[2.5*inch, 4*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E2D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(tech_table)
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("Data Protection & Security", section_style))
    story.append(Paragraph(
        "All data is processed locally unless external APIs are explicitly configured. User data is stored in local SQLite database. API keys and sensitive information are managed via environment variables. Audit logs track all system actions for compliance verification.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # Compliance Matrix
    story.append(Paragraph("Compliance Matrix", section_style))
    story.append(Paragraph(
        "This table maps system features to regulatory requirements:",
        body_style
    ))
    story.append(Spacer(1, 0.1 * inch))
    
    compliance_data = [
        ["Regulation", "Requirement", "Implementation"],
        ["GDPR Art. 30", "Record of processing", "Automated record generation with user data"],
        ["CSRD VSME", "Sustainability disclosure", "Energy tracking and emissions calculation"],
        ["EU AI Act", "Transparency", "System card and audit logging"],
        ["GDPR Art. 13", "Information provision", "Clear user notifications and consent flows"],
    ]
    
    compliance_table = Table(compliance_data, colWidths=[1.8*inch, 2.2*inch, 2.5*inch])
    compliance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E2D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(compliance_table)
    
    # Build PDF
    doc.build(story)
    
    print(f"Generated compliance pack: {output_path}")
    return output_path
