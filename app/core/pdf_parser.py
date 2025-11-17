"""
PDF Form Parser - Enhanced field extraction
Adapted from SmartPdfFiller with Tesseract integration and semantic mapping
"""
import os
from typing import Dict, List, Optional, Tuple
from pypdf import PdfReader
import pytesseract
from PIL import Image
import io
import re
from sentence_transformers import SentenceTransformer
import numpy as np

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not available. Install with: pip install pdf2image")


class PDFParser:
    """Parse PDF forms to extract fields, labels, and structure."""
    
    def __init__(self, embed_model: Optional[SentenceTransformer] = None):
        """
        Initialize PDF parser.
        
        Args:
            embed_model: Optional embedding model for semantic field matching
        """
        self.embed_model = embed_model
        self.field_patterns = {
            'name': ['name', 'company', 'organization', 'firm'],
            'address': ['address', 'street', 'location', 'postal'],
            'email': ['email', 'e-mail', 'mail'],
            'phone': ['phone', 'telephone', 'tel', 'mobile'],
            'date': ['date', 'dob', 'birth'],
            'kwh': ['kwh', 'kilowatt', 'energy', 'consumption'],
            'emissions': ['emission', 'co2', 'carbon', 'tco2e', 'co2e'],
            'amount': ['amount', 'total', 'sum', 'value', 'price'],
        }
    
    def pdf_to_image(self, pdf_path: str, page_num: int = 0, dpi: int = 300) -> Tuple[Optional[Image.Image], str]:
        """
        Convert PDF page to PIL Image.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            dpi: Resolution for conversion
            
        Returns:
            Tuple of (PIL Image, extracted text)
        """
        try:
            reader = PdfReader(pdf_path)
            if page_num >= len(reader.pages):
                page_num = 0
            
            page = reader.pages[page_num]
            
            # Try to extract text directly first
            text = page.extract_text()
            if text.strip():
                # Try to get image if pdf2image is available
                if PDF2IMAGE_AVAILABLE:
                    try:
                        images = convert_from_path(pdf_path, dpi=dpi, first_page=page_num+1, last_page=page_num+1)
                        if images:
                            return images[0], text
                    except Exception as e:
                        print(f"pdf2image conversion error: {e}")
                return None, text
            
            # Fallback to OCR if no text
            if PDF2IMAGE_AVAILABLE:
                try:
                    images = convert_from_path(pdf_path, dpi=dpi, first_page=page_num+1, last_page=page_num+1)
                    if images:
                        return images[0], ""
                except Exception as e:
                    print(f"pdf2image error: {e}")
            
            return None, ""
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None, ""
    
    def extract_text_with_ocr(self, pdf_path: str, use_ocr: bool = True) -> Dict[str, any]:
        """
        Extract text from PDF with optional OCR fallback.
        
        Args:
            pdf_path: Path to PDF file
            use_ocr: Whether to use OCR if text extraction fails
            
        Returns:
            Dictionary with text content, pages, and metadata
        """
        text_content = []
        all_text = []
        
        try:
            reader = PdfReader(pdf_path)
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
                    all_text.append(text)
                elif use_ocr:
                    # Try OCR for this page
                    img, ocr_text = self.pdf_to_image(pdf_path, page_num)
                    if img:
                        try:
                            ocr_text = pytesseract.image_to_string(img, lang='eng+deu')
                            if ocr_text.strip():
                                text_content.append(ocr_text)
                                all_text.append(ocr_text)
                        except Exception as e:
                            print(f"OCR error on page {page_num}: {e}")
            
            return {
                "text_content": '\n'.join(text_content),
                "pages": all_text,
                "page_count": len(reader.pages),
                "has_text": len(text_content) > 0
            }
        except Exception as e:
            print(f"Error extracting text: {e}")
            return {"text_content": "", "pages": [], "page_count": 0, "has_text": False}
    
    def extract_form_fields(self, pdf_path: str, use_ocr: bool = False) -> Dict[str, any]:
        """
        Extract form field labels and structure from PDF.
        Enhanced version with better pattern matching.
        
        Args:
            pdf_path: Path to PDF file
            use_ocr: Whether to use OCR for field extraction
            
        Returns:
            Dictionary with labels, fields, text content, and metadata
        """
        labels = []
        fields = []
        text_content = []
        
        # First, try to extract text
        text_data = self.extract_text_with_ocr(pdf_path, use_ocr=use_ocr)
        text_content = text_data.get("pages", [])
        
        # Extract potential field labels
        for page_text in text_content:
            lines = page_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Pattern matching for field labels
                # Lines ending with colon, question mark, or containing field keywords
                is_label = (
                    line.endswith(':') or 
                    line.endswith('?') or
                    any(keyword in line.lower() for keywords in self.field_patterns.values() for keyword in keywords)
                )
                
                if is_label:
                    labels.append(line)
                    
                    # Try to identify field type
                    field_type = self._identify_field_type(line)
                    if field_type:
                        fields.append({
                            "label": line,
                            "type": field_type,
                            "required": "required" in line.lower() or "*" in line
                        })
        
        # Also try to extract form fields from PDF structure (if available)
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                if '/Annots' in page:
                    annotations = page['/Annots']
                    for annotation in annotations:
                        obj = annotation.get_object()
                        if obj.get('/Subtype') == '/Widget':  # Form field
                            field_name = obj.get('/T', '')
                            field_type = obj.get('/FT', '')
                            if field_name:
                                fields.append({
                                    "label": field_name,
                                    "type": str(field_type),
                                    "required": False,
                                    "is_form_field": True
                                })
        except Exception as e:
            print(f"Error extracting PDF form fields: {e}")
        
        return {
            "labels": list(set(labels))[:100],  # Limit and deduplicate
            "fields": fields,
            "text_content": '\n'.join(text_content),
            "page_count": text_data.get("page_count", 0),
            "has_form_fields": any(f.get("is_form_field", False) for f in fields)
        }
    
    def _identify_field_type(self, label: str) -> Optional[str]:
        """Identify field type from label text."""
        label_lower = label.lower()
        
        for field_type, keywords in self.field_patterns.items():
            if any(keyword in label_lower for keyword in keywords):
                return field_type
        
        return None
    
    def semantic_field_mapping(self, extracted_fields: List[str], user_data: Dict, slots: Dict) -> Dict[str, any]:
        """
        Map extracted fields to user data using semantic similarity.
        
        Args:
            extracted_fields: List of extracted field labels
            user_data: User profile data
            slots: Intent slots from conversation
            
        Returns:
            Dictionary mapping field names to values
        """
        if not self.embed_model:
            # Fallback to keyword matching
            return self._keyword_field_mapping(extracted_fields, user_data, slots)
        
        # Semantic matching with embeddings
        try:
            # Embed extracted fields
            field_embeddings = self.embed_model.encode(extracted_fields, show_progress_bar=False)
            
            # Create canonical field names and embed them
            canonical_fields = list(self.field_patterns.keys()) + list(user_data.keys()) + list(slots.keys())
            canonical_embeddings = self.embed_model.encode(canonical_fields, show_progress_bar=False)
            
            # Find best matches using cosine similarity
            field_values = {}
            for i, field in enumerate(extracted_fields):
                field_emb = field_embeddings[i]
                similarities = np.dot(canonical_embeddings, field_emb)
                best_match_idx = np.argmax(similarities)
                best_match = canonical_fields[best_match_idx]
                similarity = similarities[best_match_idx]
                
                # If similarity is high enough, map the value
                if similarity > 0.6:
                    if best_match in user_data:
                        field_values[field] = user_data[best_match]
                    elif best_match in slots:
                        field_values[field] = slots[best_match]
                    elif best_match in self.field_patterns:
                        # Try to infer value from context
                        inferred = self._infer_value(best_match, user_data, slots)
                        if inferred:
                            field_values[field] = inferred
            
            return {"fieldValues": field_values, "lowConfidence": []}
        except Exception as e:
            print(f"Error in semantic mapping: {e}")
            return self._keyword_field_mapping(extracted_fields, user_data, slots)
    
    def _keyword_field_mapping(self, extracted_fields: List[str], user_data: Dict, slots: Dict) -> Dict[str, any]:
        """Fallback keyword-based field mapping."""
        field_values = {}
        
        for field in extracted_fields:
            field_lower = field.lower()
            
            # Check against patterns
            for field_type, keywords in self.field_patterns.items():
                if any(keyword in field_lower for keyword in keywords):
                    if field_type in user_data:
                        field_values[field] = user_data[field_type]
                    elif field_type in slots:
                        field_values[field] = slots[field_type]
                    break
            
            # Direct user_data match
            for key, value in user_data.items():
                if key.lower() in field_lower or field_lower in key.lower():
                    field_values[field] = value
                    break
        
        return {"fieldValues": field_values, "lowConfidence": []}
    
    def _infer_value(self, field_type: str, user_data: Dict, slots: Dict) -> Optional[any]:
        """Infer field value from context (e.g., calculate emissions from kWh)."""
        if field_type == 'emissions' and 'kWh' in slots:
            # Calculate emissions from kWh
            from utils import calculate_emissions
            result = calculate_emissions(slots['kWh'])
            return result.get('tCO2e')
        
        return None

