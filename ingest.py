import pytesseract
from pypdf import PdfReader
from PIL import Image
import io
import os
import sqlite3
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Initialize embedding model
embed_model = SentenceTransformer('intfloat/multilingual-e5-large')
dimension = 1024

# Initialize FAISS index
index = faiss.IndexFlatL2(dimension)

def pdf_to_image(pdf_path, page_num=0):
    """Convert PDF page to PIL Image."""
    try:
        reader = PdfReader(pdf_path)
        if page_num >= len(reader.pages):
            page_num = 0
        
        page = reader.pages[page_num]
        
        # Try to extract text directly first
        text = page.extract_text()
        if text.strip():
            return None, text  # Return text directly if available
        
        # Fallback to OCR if no text
        try:
            # Convert page to image (requires pdf2image or similar)
            # For now, we'll use a workaround with reportlab
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            import tempfile
            
            # This is a simplified approach - in production, use pdf2image
            return None, ""
        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            return None, ""
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None, ""

def extract_form_fields(pdf_path, use_ocr=False):
    """Extract form field labels and structure from PDF."""
    labels = []
    text_content = []
    
    try:
        reader = PdfReader(pdf_path)
        
        # Extract text from all pages
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content.append(text)
                # Simple extraction of potential field labels (lines ending with colon or question mark)
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line.endswith(':') or line.endswith('?') or 
                                any(keyword in line.lower() for keyword in ['name', 'address', 'email', 'date', 'amount', 'kwh', 'emissions'])):
                        labels.append(line)
        
        # If no text found and OCR is enabled, try OCR
        if not text_content and use_ocr:
            img, ocr_text = pdf_to_image(pdf_path)
            if ocr_text:
                text_content.append(ocr_text)
                lines = ocr_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        labels.append(line)
        
        return {
            "labels": labels[:50],  # Limit to first 50 labels
            "text_content": '\n'.join(text_content),
            "page_count": len(reader.pages)
        }
    except Exception as e:
        print(f"Error extracting form fields: {e}")
        return {"labels": [], "text_content": "", "page_count": 0}

def embed_and_index_form(form_id, form_name, labels, db_path='db.sqlite'):
    """Embed form labels and store in FAISS index and database."""
    if not labels:
        return False
    
    # Embed labels
    embeddings = embed_model.encode(labels, show_progress_bar=False)
    
    # Add to FAISS index
    if len(embeddings.shape) == 1:
        embeddings = embeddings.reshape(1, -1)
    
    # Normalize for FAISS
    faiss.normalize_L2(embeddings)
    index.add(embeddings.astype('float32'))
    
    # Store in database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Store form template
    import json
    c.execute('''
        INSERT OR REPLACE INTO FormTemplate (form_id, form_name, form_type, field_mappings)
        VALUES (?, ?, ?, ?)
    ''', (form_id, form_name, 'pdf', json.dumps(labels)))
    
    conn.commit()
    conn.close()
    
    return True

def ingest_form(pdf_path, form_id, form_name):
    """Main ingestion function: extract fields and index form."""
    print(f"Ingesting form: {form_id} from {pdf_path}")
    
    # Extract fields
    result = extract_form_fields(pdf_path, use_ocr=True)
    
    if not result['labels']:
        print(f"Warning: No labels extracted from {pdf_path}")
        return result
    
    # Index form
    success = embed_and_index_form(form_id, form_name, result['labels'])
    
    if success:
        print(f"Successfully indexed {len(result['labels'])} fields for {form_id}")
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python ingest.py <pdf_path> <form_id> <form_name>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    form_id = sys.argv[2]
    form_name = sys.argv[3]
    
    result = ingest_form(pdf_path, form_id, form_name)
    print(f"Extracted {len(result['labels'])} labels")
