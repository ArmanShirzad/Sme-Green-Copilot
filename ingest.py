import pytesseract
from pypdf import PdfReader
from PIL import Image
import io
import os
import sqlite3
import json
from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv

load_dotenv()

embed_model = None
faiss_index = None
dimension = 1024

def init_models():
    global embed_model, faiss_index
    try:
        embed_model = SentenceTransformer('intfloat/multilingual-e5-large')
        faiss_index = faiss.IndexFlatL2(dimension)
        print("Models initialized for ingestion")
    except Exception as e:
        print(f"Model initialization error: {e}")

init_models()

def ingest_form(pdf_path, form_id=None, form_name=None, form_type=None):
    """Ingest a PDF form template and extract field labels"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    reader = PdfReader(pdf_path)
    labels = []
    text_content = []
    
    print(f"Processing {len(reader.pages)} pages...")
    
    for page_num, page in enumerate(reader.pages[:5]):
        try:
            text = page.extract_text()
            if text:
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text_content.extend(lines)
                labels.extend(lines)
        except Exception as e:
            print(f"Text extraction error on page {page_num}: {e}")
        
        try:
            if hasattr(page, 'to_image'):
                img = page.to_image(resolution=150)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                pil_img = Image.open(img_byte_arr)
                ocr_data = pytesseract.image_to_data(pil_img, output_type='dict')
                ocr_text = [item for item in ocr_data.get('text', []) if item.strip()]
                labels.extend(ocr_text)
        except Exception as e:
            print(f"OCR error on page {page_num}: {e}")
    
    labels = list(set([l for l in labels if len(l) > 2]))[:100]
    
    if embed_model and labels:
        try:
            label_embeddings = embed_model.encode(labels, normalize_embeddings=True)
            if faiss_index.ntotal == 0:
                faiss_index.add(label_embeddings)
            else:
                faiss_index.add(label_embeddings)
            print(f"Added {len(labels)} labels to FAISS index")
        except Exception as e:
            print(f"Embedding error: {e}")
    
    form_id = form_id or os.path.basename(pdf_path).replace('.pdf', '')
    form_name = form_name or form_id
    form_type = form_type or 'generic'
    
    db_path = os.getenv('DB_PATH', 'db.sqlite')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        INSERT OR REPLACE INTO FormTemplate (form_id, form_name, form_type, fields, template_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        form_id,
        form_name,
        form_type,
        json.dumps(labels),
        pdf_path
    ))
    
    conn.commit()
    conn.close()
    
    print(f"Ingested form: {form_id} ({len(labels)} fields)")
    
    return {
        "formId": form_id,
        "formName": form_name,
        "formType": form_type,
        "labels": labels,
        "fieldCount": len(labels)
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <pdf_path> [form_id] [form_name] [form_type]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    form_id = sys.argv[2] if len(sys.argv) > 2 else None
    form_name = sys.argv[3] if len(sys.argv) > 3 else None
    form_type = sys.argv[4] if len(sys.argv) > 4 else None
    
    result = ingest_form(pdf_path, form_id, form_name, form_type)
    print(f"\nIngestion complete:")
    print(f"  Form ID: {result['formId']}")
    print(f"  Fields extracted: {result['fieldCount']}")
