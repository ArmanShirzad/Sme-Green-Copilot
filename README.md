# Green SME Compliance Co-Pilot

An AI agent system that automates ESG audits and compliance filings (CSRD/GDPR/EU AI Act) for small and medium enterprises through semantic form mapping and regulatory reasoning.

## Overview

The Green SME Compliance Co-Pilot helps SMEs navigate complex regulatory requirements by:
- Automatically detecting compliance needs from natural language input
- Mapping form fields using semantic embeddings (handles form variations)
- Estimating emissions and generating ESG insights
- Filling compliance forms and generating compliance packs
- Sending completed documents via email

## Architecture

```
┌─────────────┐
│   Chat UI   │ (OpenWebUI)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  FastAPI Brain  │ (Intent Detection, Workflow Selection)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Core Services  │ (Field Mapping, PDF Filling, Emissions)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Ingestion     │ (OCR, Form Template Processing)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Automations    │ (Email via n8n, Storage via MinIO)
└─────────────────┘
```

## Features

### MVP Recipes (3)

1. **CSRD Energy Audit**
   - Processes energy consumption data
   - Estimates CO2 emissions
   - Generates VSME snapshot and disclosure letter
   - Compliance: CSRD VSME, ESRS E1

2. **GDPR Article 30 Export**
   - Extracts data processing information
   - Maps controller details, purposes, categories
   - Generates Art.30 processing record
   - Compliance: GDPR Art.30

3. **EU AI Act Risk Check**
   - Assesses AI system risks
   - Classifies risk levels
   - Generates system card and transparency logs
   - Compliance: EU AI Act

### Core Capabilities

- **Semantic Form Mapping**: Uses multilingual embeddings to map form fields across variations
- **Emissions Estimation**: Calculates CO2 emissions from energy consumption using country-specific grid factors
- **PDF Generation**: Fills forms and creates compliance packs using ReportLab
- **OCR Support**: Extracts text from PDF forms using Tesseract
- **Audit Trail**: Maintains complete logs for compliance transparency

## Quick Start

### Prerequisites

- Python 3.12+
- Tesseract OCR (for PDF parsing)
- Docker (optional, for OpenWebUI/MinIO/n8n)

### Installation

1. **Clone and setup environment:**

```bash
git clone <repository-url>
cd green-sme-compliance-copilot
./setup.sh
```

Or manually:

```bash
python3 -m venv green-agent-env
source green-agent-env/bin/activate
pip install -r requirements.txt
python db_init.py
```

2. **Install Tesseract OCR:**

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Verify
tesseract --version
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENWEATHER_API_KEY (get free key from openweathermap.org)
# - MISTRAL_API_KEY (optional, for enhanced intent detection)
# - N8N_WEBHOOK_URL (if using n8n for email)
```

4. **Start the API server:**

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

5. **Test the API:**

```bash
python test_api.py
```

### Optional: Docker Services

Start OpenWebUI, MinIO, and n8n:

```bash
docker-compose up -d
```

- OpenWebUI: http://localhost:3000
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- n8n: http://localhost:5678

## Usage

### API Endpoints

#### Detect Intent
```bash
POST /tools/detectIntent
{
  "text": "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month."
}
```

#### Select Workflow
```bash
POST /tools/selectWorkflow
{
  "intentType": "energyAuditForCSRD",
  "slots": {"kWh": 3000, "city": "Flensburg"}
}
```

#### Estimate Emissions
```bash
POST /tools/estimateEmissions
{
  "kWh": 3000,
  "country": "DE"
}
```

#### Fill PDF
```bash
POST /tools/fillPdf
{
  "formId": "vsme_snapshot",
  "fieldValues": {
    "companyName": "Prime Bakery",
    "kWh": 3000,
    "tCO2e": 1.26
  },
  "formType": "vsme_snapshot"
}
```

#### Execute Complete Workflow
```bash
POST /workflow/execute
{
  "text": "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month.",
  "userId": 1
}
```

### Form Ingestion

To add a new form template:

```bash
python ingest.py templates/your_form.pdf form_id "Form Name" form_type
```

Example:
```bash
python ingest.py templates/vsme_snapshot.pdf vsme_snapshot "CSRD VSME Snapshot" csrd
```

### OpenWebUI Integration

1. Start OpenWebUI: `docker-compose up -d`
2. Access http://localhost:3000
3. Configure model to use FastAPI tools
4. Use system prompt:

```
You are a Green SME Compliance Co-Pilot. Help users with:
- CSRD energy audits and emissions reporting
- GDPR Article 30 processing records
- EU AI Act risk assessments

Use the FastAPI tools at http://localhost:8000 to:
- Detect compliance needs (/tools/detectIntent)
- Execute workflows (/workflow/execute)
- Generate compliance documents

Always maintain transparency and provide audit trails per EU AI Act requirements.
```

## Project Structure

```
.
├── main.py                 # FastAPI backend with all endpoints
├── utils.py                # ESG and compliance utility functions
├── db_init.py              # Database initialization
├── ingest.py               # Form template ingestion script
├── test_api.py             # API testing script
├── setup.sh                # Setup script
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker services configuration
├── .env.example           # Environment variables template
├── config/
│   └── compliance_matrix.yaml  # Regulatory mappings and recipes
├── templates/              # PDF form templates (add your own)
└── outputs/                # Generated PDFs and compliance packs
```

## Data Model

### UserProfile
- id, name, address, email, phone, IBAN, business_facts

### Submission
- id, userId, intent, selected_forms, answers, files, status, audit_trail

### FormTemplate
- id, form_id, form_name, form_type, fields, template_path

### CompliancePack
- id, submission_id, pack_type, file_path, regulations

## Compliance Features

### GDPR Art.30
- Controller details extraction
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

## Development

### Adding New Recipes

1. Add recipe to `config/compliance_matrix.yaml`
2. Implement workflow logic in `main.py`
3. Add form templates to `templates/`
4. Test with `test_api.py`

### Adding New Regulations

1. Update `compliance_matrix.yaml` with regulation details
2. Add field mappings if needed
3. Update compliance pack generation in `utils.py`

## Testing

Run the test suite:

```bash
python test_api.py
```

Or test individual endpoints:

```bash
# Start server first
uvicorn main:app --reload

# In another terminal
curl -X POST http://localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "I need CSRD compliance help"}'
```

## Troubleshooting

### Tesseract OCR Errors
- Ensure Tesseract is installed: `tesseract --version`
- For PDF parsing issues, fallback to text extraction is automatic

### Model Loading Errors
- First run downloads models (~500MB), ensure internet connection
- Models cached in `~/.cache/huggingface/`

### Database Errors
- Run `python db_init.py` to recreate database
- Check `DB_PATH` in `.env`

### API Connection Errors
- Ensure server is running: `uvicorn main:app --reload`
- Check port 8000 is not in use

## Deployment

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **Database**: Migrate from SQLite to PostgreSQL for production
3. **Storage**: Configure MinIO or S3 for document storage
4. **API Keys**: Rotate keys regularly, use environment-specific keys
5. **Logging**: Implement structured logging (e.g., Python logging module)
6. **Monitoring**: Add health checks and metrics endpoints

### Docker Deployment

```bash
# Build image
docker build -t green-compliance-copilot .

# Run container
docker run -p 8000:8000 --env-file .env green-compliance-copilot
```

## License

MIT License - See LICENSE file for details

## Contributing

1. Keep skills modular and single-purpose
2. Write unit tests for each component
3. Document data sources and assumptions
4. Maintain audit trails for compliance features

## Support

For issues or questions:
- Check troubleshooting section
- Review API documentation at `/docs` (Swagger UI)
- Contact team lead for Agenthathon demo questions

## Roadmap

Post-MVP extensions:
- Full DPIA (Data Protection Impact Assessment) via chained prompts
- Evidence folder generation via n8n zips
- Additional regulation support (e.g., German Energie Audit)
- Enhanced OCR with form field detection
- Multi-language support expansion
- Integration with ERP systems

## Acknowledgments

Built for OPEN Agentathon (Nov 17, 2025) - 3-hour MVP build session.
