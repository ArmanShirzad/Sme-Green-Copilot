"""
PDF Form Filler - True PDF form filling (not text overlay)
Adapted from SmartPdfFiller with handwriting fonts and precise positioning
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

try:
    from PyPDFForm import PdfWrapper
    PYPDFFORM_AVAILABLE = True
except ImportError:
    PYPDFFORM_AVAILABLE = False
    print("Warning: PyPDFForm not available. Install with: pip install PyPDFForm")
    print("Falling back to ReportLab text overlay.")


class PDFFiller:
    """Fill PDF forms with precise positioning and handwriting-style fonts."""
    
    def __init__(self, use_handwriting_font: bool = False):
        """
        Initialize PDF filler.
        
        Args:
            use_handwriting_font: Whether to use handwriting-style font for "official" look
        """
        self.use_handwriting_font = use_handwriting_font
        self._load_fonts()
    
    def _load_fonts(self):
        """Load handwriting fonts if available."""
        if self.use_handwriting_font:
            # Try to load handwriting fonts (optional)
            # You can download fonts like "Kalam" or "Caveat" and register them
            try:
                # Example: Register a handwriting font if available
                # font_path = "fonts/Kalam-Regular.ttf"
                # if os.path.exists(font_path):
                #     pdfmetrics.registerFont(TTFont('Handwriting', font_path))
                pass
            except Exception as e:
                print(f"Could not load handwriting font: {e}")
                self.use_handwriting_font = False
    
    def fill_pdf_form(self, template_path: str, field_values: Dict[str, any], 
                     output_path: Optional[str] = None) -> str:
        """
        Fill PDF form with field values using true form filling.
        
        Args:
            template_path: Path to PDF template
            field_values: Dictionary mapping field names to values
            output_path: Optional output path (auto-generated if not provided)
            
        Returns:
            Path to filled PDF
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        # Generate output path if not provided
        if not output_path:
            os.makedirs('outputs', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.splitext(os.path.basename(template_path))[0]
            output_path = f"outputs/filled_{base_name}_{timestamp}.pdf"
        
        # Try PyPDFForm first (true form filling)
        if PYPDFFORM_AVAILABLE:
            try:
                return self._fill_with_pypdfform(template_path, field_values, output_path)
            except Exception as e:
                print(f"PyPDFForm filling failed: {e}, falling back to ReportLab")
        
        # Fallback to ReportLab with precise positioning
        return self._fill_with_reportlab(template_path, field_values, output_path)
    
    def _fill_with_pypdfform(self, template_path: str, field_values: Dict, output_path: str) -> str:
        """Fill PDF using PyPDFForm (true form fields)."""
        pdf = PdfWrapper(template_path, adobe_mode=True)
        
        # Fill form fields
        filled_pdf = pdf.fill(field_values)
        
        # Save filled PDF
        filled_pdf.write(output_path)
        
        return output_path
    
    def _fill_with_reportlab(self, template_path: str, field_values: Dict, output_path: str) -> str:
        """
        Fill PDF using ReportLab with precise positioning.
        This overlays text on the original PDF.
        """
        # Read original PDF
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        # Create overlay canvas
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        width, height = A4
        
        # Use handwriting font if available
        font_name = 'Handwriting' if self.use_handwriting_font else 'Helvetica'
        font_size = 10
        
        try:
            can.setFont(font_name, font_size)
        except:
            can.setFont('Helvetica', font_size)
        
        # Position fields (this is a simplified version - in production,
        # you'd use the parser to get exact coordinates)
        y_start = height - 100
        y = y_start
        x = 100
        
        for field_name, value in field_values.items():
            if y < 50:
                can.showPage()
                y = y_start
            
            # Draw field value
            can.drawString(x, y, f"{field_name}: {str(value)}")
            y -= 20
        
        can.save()
        
        # Merge overlay with original PDF
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        
        for page_num, page in enumerate(reader.pages):
            if page_num < len(overlay_pdf.pages):
                page.merge_page(overlay_pdf.pages[page_num])
            writer.add_page(page)
        
        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def fill_with_coordinates(self, template_path: str, field_mappings: List[Dict], 
                             output_path: Optional[str] = None) -> str:
        """
        Fill PDF with precise coordinate-based positioning.
        
        Args:
            template_path: Path to PDF template
            field_mappings: List of dicts with 'field', 'value', 'x', 'y', 'page'
            output_path: Optional output path
            
        Returns:
            Path to filled PDF
        """
        if not output_path:
            os.makedirs('outputs', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.splitext(os.path.basename(template_path))[0]
            output_path = f"outputs/filled_{base_name}_{timestamp}.pdf"
        
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        # Group fields by page
        pages_fields = {}
        for mapping in field_mappings:
            page_num = mapping.get('page', 0)
            if page_num not in pages_fields:
                pages_fields[page_num] = []
            pages_fields[page_num].append(mapping)
        
        # Create overlay for each page
        for page_num in range(len(reader.pages)):
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            
            # Draw fields for this page
            if page_num in pages_fields:
                for mapping in pages_fields[page_num]:
                    x = mapping.get('x', 100)
                    y = mapping.get('y', 100)
                    value = str(mapping.get('value', ''))
                    font_size = mapping.get('font_size', 10)
                    
                    can.setFont('Helvetica', font_size)
                    can.drawString(x, y, value)
            
            can.save()
            packet.seek(0)
            overlay_pdf = PdfReader(packet)
            
            # Merge with original page
            page = reader.pages[page_num]
            if overlay_pdf.pages:
                page.merge_page(overlay_pdf.pages[0])
            writer.add_page(page)
        
        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path
    
    def add_esg_chart(self, pdf_path: str, chart_data: Dict, output_path: Optional[str] = None) -> str:
        """
        Add ESG chart (e.g., emissions pie chart) to PDF using ReportLab.
        
        Args:
            pdf_path: Path to existing PDF
            chart_data: Dictionary with chart data (type, values, labels)
            output_path: Optional output path
            
        Returns:
            Path to PDF with chart
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = f"outputs/{base_name}_with_chart_{timestamp}.pdf"
        
        # Read original PDF
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Create chart page
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        width, height = A4
        
        # Draw chart title
        can.setFont("Helvetica-Bold", 16)
        can.drawString(50, height - 50, chart_data.get('title', 'ESG Chart'))
        
        # Draw simple bar chart (simplified - in production use matplotlib or similar)
        chart_type = chart_data.get('type', 'bar')
        values = chart_data.get('values', [])
        labels = chart_data.get('labels', [])
        
        if chart_type == 'bar' and values:
            max_value = max(values)
            bar_width = 50
            x_start = 100
            y_start = height - 150
            
            for i, (label, value) in enumerate(zip(labels, values)):
                x = x_start + (i * (bar_width + 20))
                bar_height = (value / max_value) * 200
                
                # Draw bar
                can.setFillColorRGB(0.2, 0.6, 0.8)
                can.rect(x, y_start, bar_width, bar_height, fill=1)
                
                # Draw label
                can.setFont("Helvetica", 8)
                can.drawString(x, y_start - 20, label[:10])
                can.drawString(x, y_start - 35, str(value))
        
        can.save()
        packet.seek(0)
        chart_pdf = PdfReader(packet)
        
        # Add all original pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Add chart page
        if chart_pdf.pages:
            writer.add_page(chart_pdf.pages[0])
        
        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return output_path

