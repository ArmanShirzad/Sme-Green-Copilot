# Green SME Compliance Co-Pilot

An AI agent system that automates ESG audits and compliance filings (CSRD/GDPR/EU AI Act) for small and medium enterprises through semantic mapping and regulatory reasoning.

## Overview

The Green SME Compliance Co-Pilot helps SMEs navigate complex regulatory requirements by:

- Automating energy audits and emissions calculations for CSRD compliance
- Generating GDPR Article 30 processing records
- Assessing AI system risks per EU AI Act requirements
- Using semantic mapping to handle form variations
- Generating compliance packs with regulatory mappings

## Architecture

The system consists of five tiers:

1. **Interface**: Chat interface (OpenWebUI integration)
2. **Brain**: Logic/router layer (FastAPI endpoints)
3. **Services**: Core functions (emissions, form filling, compliance generation)
4. **Ingestion**: Form parsing and semantic indexing
5. **Automations**: Email delivery and file exports (n8n integration)

## MVP Recipes

1. **CSRD Energy Audit**: Complete CSRD VSME snapshot with energy audit data
2. **GDPR Article 30 Export**: Generate GDPR Article 30 processing record
3. **EU AI Act Risk Check**: Assess AI system risks per EU AI Act requirements

## Prerequisites

- Python 3.12+
- Tesseract OCR (for PDF text extraction)
- Docker (optional, for OpenWebUI/n8n/MinIO)

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y tesseract-ocr python3.12-venv
```

**macOS:**
```bash
brew install tesseract
```

## Installation

### 1. Clone and Setup Environment

```bash
# Create virtual environment
python3.12 -m venv green-agent-env
source green-agent-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
DB_PATH=db.sqlite
OPENWEATHER_API_KEY=your_openweather_api_key_here
GROQ_API_KEY=your_groq_api_key_here  # Optional
N8N_WEBHOOK_URL=http://localhost:5678/webhook/compliance-email  # Optional
```

### 3. Initialize Database

```bash
python db_init.py
```

This creates the SQLite database with required tables and a mock user profile.

### 4. Download Form Templates (Manual Step)

Before running, download the following templates to the `templates/` directory:

1. **CSRD VSME Standard**: Download from [EFRAG VSME Standard](https://www.efrag.org/sites/default/files/sites/webpublishing/SiteAssets/VSME%20Standard.pdf)
2. **GDPR Article 30**: Create a blank template or use the structure from GDPR guidelines
3. **EU AI Act Risk Worksheet**: Download from [EU AI Act resources](https://artificialintelligenceact.eu)

### 5. Ingest Form Templates (Optional)

To enable semantic form mapping, ingest your templates:

```bash
python ingest.py templates/vsme_snapshot.pdf vsme_snapshot "CSRD VSME Snapshot"
python ingest.py templates/gdpr_art30.pdf gdpr_art30 "GDPR Article 30 Record"
python ingest.py templates/ai_act_risk.pdf ai_act_risk "EU AI Act Risk Worksheet"
```

## Running the Application

### Start the FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Optional: Start Supporting Services

**OpenWebUI (Chat Interface):**
```bash
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

**n8n (Workflow Automation):**
```bash
npm install -g n8n
n8n start
```

**MinIO (Object Storage):**
```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  --name minio \
  minio/minio server /data --console-address ":9001"
```

## Usage

### API Endpoints

#### Detect Intent
```bash
curl -X POST "http://localhost:8000/tools/detectIntent" \
  -H "Content-Type: application/json" \
  -d '{"text": "I need an energy audit for CSRD compliance"}'
```

#### Estimate Emissions
```bash
curl -X POST "http://localhost:8000/tools/estimateEmissions" \
  -H "Content-Type: application/json" \
  -d '{"kWh": 3000, "country": "DE"}'
```

#### Generate Compliance Pack
```bash
curl -X POST "http://localhost:8000/tools/generateCompliancePack" \
  -H "Content-Type: application/json" \
  -d '{"submissionId": 1, "recipeId": "csrd_audit", "regulations": ["CSRD", "ESRS E1"]}'
```

### Example Workflow

1. User sends chat message: "I need an energy audit for CSRD"
2. System detects intent: `energyAuditForCSRD`
3. System selects workflow: `csrd_audit` recipe
4. System collects missing data (kWh, city)
5. System estimates emissions
6. System fills VSME form
7. System generates compliance pack
8. System exports PDF and sends email

## Project Structure

```
/workspace
├── main.py                 # FastAPI application
├── utils.py                # ESG and regulation utilities
├── ingest.py               # Form ingestion and OCR
├── db_init.py              # Database initialization
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── config/
│   ├── recipes.yaml        # Workflow recipes
│   └── regulations.yaml    # Regulatory mappings
├── templates/              # Form templates (download manually)
├── data/                   # Data storage
└── outputs/                # Generated PDFs and compliance packs
```

## Configuration

### Recipes (`config/recipes.yaml`)

Defines workflow recipes for different compliance tasks. Each recipe includes:
- Intent patterns
- Required forms
- Workflow steps
- Associated regulations

### Regulations (`config/regulations.yaml`)

Maps regulatory requirements to form fields and compliance pack sections.

## Development

### Testing

Test individual endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Test intent detection
curl -X POST http://localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "GDPR Article 30 record"}'
```

### Adding New Recipes

1. Add recipe definition to `config/recipes.yaml`
2. Implement any new tools in `main.py`
3. Update regulatory mappings in `config/regulations.yaml`

### Adding New Forms

1. Place PDF template in `templates/`
2. Run ingestion: `python ingest.py templates/new_form.pdf form_id "Form Name"`
3. Update recipe to include new form

## Troubleshooting

### Tesseract OCR Not Found

Install Tesseract:
- Ubuntu: `sudo apt install tesseract-ocr`
- macOS: `brew install tesseract`

### Embedding Model Download Issues

The first run will download the multilingual-e5-large model (~1.3GB). Ensure stable internet connection.

### Database Locked

If SQLite shows "database is locked", ensure only one process is accessing the database at a time.

## Limitations (MVP)

- Mock LLM responses if Groq API key not configured
- Simplified form filling (ReportLab-based, not true PDF form filling)
- Basic OCR (Tesseract fallback if PDF text extraction fails)
- Local file storage (MinIO integration optional)

## Post-Event Extensions

Planned enhancements:
- Full DPIA workflow via chained prompts
- Evidence folder generation via n8n zips
- Additional regulatory frameworks
- Advanced semantic matching with fine-tuned embeddings
- True PDF form filling with PyPDF2/form libraries

## License

MIT License

## Contact

For questions about the Agenthathon submission, contact the team lead.
