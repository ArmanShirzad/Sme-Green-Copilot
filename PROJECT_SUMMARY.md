# Green SME Compliance Co-Pilot - Project Summary

## What Has Been Built

A complete, production-ready blueprint for an AI agent system that automates ESG audits and compliance filings for SMEs. The system is designed for a 3-hour MVP build during the OPEN Agentathon (Nov 17, 2025).

## Core Components

### 1. FastAPI Backend (`main.py`)
- **Intent Detection**: Natural language processing to identify compliance needs
- **Workflow Selection**: Routes requests to appropriate compliance recipes
- **Field Mapping**: Semantic embeddings to map form fields across variations
- **Emissions Estimation**: Calculates CO2 emissions from energy consumption
- **PDF Generation**: Fills forms and creates compliance packs
- **OCR Support**: Extracts text from PDF forms using Tesseract
- **Complete Workflow**: End-to-end execution from chat input to document generation

### 2. Utility Modules (`utils.py`)
- Weather API integration for ESG insights
- Load shifting suggestions based on energy profiles
- Compliance pack generation with regulatory mappings
- Email sending via n8n webhooks
- Emissions calculation with country-specific grid factors

### 3. Database Layer (`db_init.py`)
- SQLite database with tables for:
  - UserProfile: Company information
  - Submission: Compliance submissions and audit trails
  - FormTemplate: Ingested form templates
  - CompliancePack: Generated compliance documents

### 4. Form Ingestion (`ingest.py`)
- OCR-based PDF parsing
- Semantic embedding extraction
- FAISS index for field matching
- Template storage in database

### 5. Configuration (`config/compliance_matrix.yaml`)
- Three MVP recipes:
  - CSRD Energy Audit
  - GDPR Article 30 Export
  - EU AI Act Risk Check
- Regulatory mappings and requirements
- Field mapping definitions

## Key Features

### Semantic Form Mapping
- Uses multilingual embeddings (`intfloat/multilingual-e5-large`)
- Handles form variations without manual mapping
- "Drop any form" scalability

### Compliance Integration
- GDPR Art.30: Controller details, processing purposes, data categories
- CSRD VSME: Energy consumption, Scope 2 emissions, methodology
- EU AI Act: System cards, risk assessment, transparency logs

### ESG Insights
- Emissions estimation with country-specific factors
- Weather-based load shifting suggestions
- Energy audit recommendations

## File Structure

```
.
├── main.py                    # FastAPI backend (all endpoints)
├── utils.py                   # ESG and compliance utilities
├── db_init.py                 # Database initialization
├── ingest.py                  # Form template ingestion
├── test_api.py                # API testing script
├── example_usage.py            # Usage examples
├── setup.sh                   # Setup script
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Docker services (OpenWebUI, MinIO)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── config/
│   └── compliance_matrix.yaml # Regulatory mappings
├── templates/                 # PDF form templates
└── outputs/                   # Generated documents
```

## API Endpoints

### Core Tools
- `POST /tools/detectIntent` - Detect compliance intent from text
- `POST /tools/selectWorkflow` - Select workflow recipe
- `POST /tools/mapFields` - Map form fields semantically
- `POST /tools/estimateEmissions` - Calculate CO2 emissions
- `POST /tools/fillPdf` - Fill PDF forms
- `POST /tools/parseForm` - Parse PDF with OCR
- `POST /tools/collectAnswers` - Collect missing field answers
- `POST /tools/exportFile` - Export to storage
- `POST /tools/emailFile` - Send email with attachment

### Workflows
- `POST /workflow/execute` - Execute complete workflow
- `GET /submissions/{id}` - Get submission details
- `GET /health` - Health check

## Setup Instructions

1. **Install dependencies:**
   ```bash
   ./setup.sh
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Add OPENWEATHER_API_KEY
   ```

3. **Initialize database:**
   ```bash
   python db_init.py
   ```

4. **Start API server:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Test:**
   ```bash
   python test_api.py
   ```

## Demo Scenarios

### Scenario 1: CSRD Energy Audit
**Input:** "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month."

**Output:**
- Detected intent: energyAuditForCSRD
- Workflow: csrd_audit
- Generated PDF: filled_vsme_snapshot.pdf
- Compliance pack: compliance_pack_*.pdf
- Emissions: 1.26 tCO2e (DE grid factor)

### Scenario 2: GDPR Article 30
**Input:** "Generate GDPR Article 30 processing record"

**Output:**
- Detected intent: gdprArticle30
- Workflow: gdpr_art30
- Generated GDPR Art.30 record PDF
- Compliance pack with regulatory details

### Scenario 3: EU AI Act Risk Check
**Input:** "Check EU AI Act compliance for our system"

**Output:**
- Detected intent: euAIActRisk
- Workflow: ai_act_check
- Risk assessment PDF
- System card generation

## Technical Stack

- **Backend**: FastAPI (Python 3.12+)
- **ML Models**: Sentence Transformers (multilingual embeddings)
- **Vector DB**: FAISS (for semantic search)
- **PDF**: ReportLab (generation), PyPDF (parsing)
- **OCR**: Tesseract
- **Database**: SQLite (production: PostgreSQL)
- **Storage**: MinIO (S3-compatible)
- **Automation**: n8n (workflows)
- **UI**: OpenWebUI (chat interface)

## Compliance Features

### GDPR Art.30
- Automated extraction of controller details
- Processing purposes mapping
- Data categories classification
- Recipients identification
- Retention period inference
- Security measures documentation

### CSRD VSME
- Energy consumption reporting
- Scope 2 emissions calculation
- Methodology disclosure
- VSME-aligned ESRS E1 compliance

### EU AI Act
- System card generation
- Risk level classification
- Transparency log maintenance
- Human oversight documentation

## Scalability

- **Semantic Mapping**: Handles form variations without manual configuration
- **Modular Architecture**: Easy to add new recipes and regulations
- **API-First**: Can integrate with any frontend
- **Extensible**: Simple to add new compliance requirements

## Post-MVP Extensions

- Full DPIA (Data Protection Impact Assessment)
- Evidence folder generation via n8n
- Additional regulations (German Energie Audit)
- Enhanced OCR with form field detection
- ERP system integrations
- Multi-language expansion

## Testing

- Unit tests: `python test_api.py`
- Examples: `python example_usage.py`
- Health check: `curl http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Deployment

- **Development**: `uvicorn main:app --reload`
- **Production**: Use Dockerfile or deploy to cloud
- **Database**: Migrate to PostgreSQL for production
- **Storage**: Configure MinIO or S3
- **Monitoring**: Add health checks and metrics

## Key Innovations

1. **Semantic Form Mapping**: No manual field mapping needed
2. **Regulatory Reasoning**: Built-in compliance logic
3. **Audit Trails**: Complete transparency for EU AI Act
4. **Modular Recipes**: Easy to extend with new compliance types
5. **ESG Integration**: Combines emissions data with compliance

## Ready for Hackathon

The system is complete and ready for the 3-hour MVP build:
- All core endpoints implemented
- Database schema defined
- Configuration files ready
- Test scripts provided
- Documentation complete
- Docker setup included

## Next Steps

1. Run `./setup.sh` to install dependencies
2. Add form templates to `templates/` directory
3. Configure `.env` with API keys
4. Start API server and test
5. Integrate with OpenWebUI for chat interface
6. Prepare demo scenarios

Good luck with the hackathon!
