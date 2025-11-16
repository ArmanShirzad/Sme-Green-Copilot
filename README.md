# Green SME Compliance Co-Pilot

**AI-powered compliance automation for small and medium enterprises**

An agentic AI system that automates ESG audits, CSRD reporting, GDPR documentation, and EU AI Act compliance through semantic form mapping and intelligent workflow orchestration.

![Status](https://img.shields.io/badge/status-hackathon--ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## Overview

Green SME Compliance Co-Pilot helps SMEs navigate complex EU regulations by:

- **Understanding natural language requests** - No need to know regulatory jargon
- **Automating document generation** - CSRD, GDPR, EU AI Act forms filled automatically
- **Calculating ESG metrics** - Energy audits, emissions, sustainability recommendations
- **Ensuring compliance** - Built-in regulatory knowledge and audit trails
- **Scaling effortlessly** - Semantic mapping works with any compliance form

### Key Features

- **3 Complete Workflows**: CSRD/VSME, GDPR Article 30, EU AI Act Risk Assessment
- **Semantic Form Mapping**: Drop any PDF form, the agent learns its structure
- **ESG Intelligence**: Emissions calculation, weather-based load shifting
- **Regulatory Reasoning**: Infers legal bases, classifies AI risks, maps requirements
- **EU AI Act Compliant**: Transparency cards, audit logging, human oversight
- **Production-Ready**: FastAPI backend, Docker deployment, comprehensive tests

## Architecture

```
┌─────────────────┐
│   Chat/API      │  OpenWebUI, REST API, CLI
└────────┬────────┘
         │
┌────────▼────────────────────────────────────┐
│         Orchestrator Brain                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Intent   │  │Workflow  │  │ Semantic │  │
│  │Detection │  │ Router   │  │ Mapper   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└────────┬────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────┐
│         Service Layer                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ESG Calc │  │PDF Gen  │  │Email    │     │
│  │Weather  │  │OCR      │  │Storage  │     │
│  └─────────┘  └─────────┘  └─────────┘     │
└────────┬────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────┐
│         Data Layer                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │SQLite   │  │FAISS    │  │MinIO    │     │
│  │Profiles │  │Vectors  │  │Docs     │     │
│  └─────────┘  └─────────┘  └─────────┘     │
└─────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional, for services)
- Tesseract OCR (for PDF parsing)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd green-sme-compliance-copilot

# Run automated setup
chmod +x setup.sh run.sh
./setup.sh

# This will:
# - Create virtual environment
# - Install dependencies
# - Initialize database
# - Create directory structure
# - Set up .env file
```

### Configuration

Edit `.env` with your API keys:

```bash
# Required
OPENWEATHER_API_KEY=your_key_here

# Optional (for enhanced NLP)
MISTRAL_API_KEY=your_key_here

# Database
DB_PATH=db.sqlite

# Storage (optional)
MINIO_URL=http://localhost:9000
```

Get OpenWeather API key (free): https://openweathermap.org/api

### Running the Application

**Option 1: Local Python**

```bash
source green-agent-env/bin/activate
./run.sh
```

**Option 2: Docker Compose**

```bash
docker-compose up -d
```

This starts:
- FastAPI backend (port 8000)
- MinIO storage (ports 9000, 9001)
- n8n automation (port 5678)
- OpenWebUI chat (port 3000)

### Testing

```bash
# Test all endpoints
./test_endpoints.sh

# Manual API test
curl http://localhost:8000/

# Visit interactive docs
open http://localhost:8000/docs
```

## Usage Examples

### 1. CSRD Energy Audit via API

```bash
# Detect intent
curl -X POST http://localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "We need CSRD report. Used 3200 kWh in Flensburg last month"}'

# Calculate emissions
curl -X POST http://localhost:8000/tools/estimateEmissions \
  -H "Content-Type: application/json" \
  -d '{"kWh": 3200, "gridFactor": 0.42}'

# Generate VSME snapshot
curl -X POST http://localhost:8000/tools/fillPdf \
  -H "Content-Type: application/json" \
  -d '{
    "formId": "vsme_snapshot",
    "fieldValues": {
      "name": "Prime Bakery GmbH",
      "city": "Flensburg",
      "kWh": 3200,
      "tCO2e": 1.34
    }
  }'

# Download generated PDF
curl http://localhost:8000/tools/downloadFile/<doc_id> -o report.pdf
```

### 2. GDPR Article 30 Record

```bash
curl -X POST http://localhost:8000/tools/fillPdf \
  -H "Content-Type: application/json" \
  -d '{
    "formId": "gdpr_art30",
    "fieldValues": {
      "name": "My Company GmbH",
      "purposes": "Customer management, invoicing",
      "data_categories": "Contact details, transaction data",
      "recipients": "Accounting service, cloud provider",
      "retention": "Contract duration + 3 years",
      "security": "Encryption, access controls, MFA"
    }
  }'
```

### 3. EU AI Act Compliance Pack

```bash
curl -X POST http://localhost:8000/tools/generateCompliancePack \
  -H "Content-Type: application/json" \
  -d '{
    "submissionId": 1,
    "regulations": ["CSRD", "GDPR", "EU_AI_Act"]
  }'
```

### 4. Chat Interface (OpenWebUI)

Visit `http://localhost:3000` and chat naturally:

```
You: I need help with a CSRD energy audit for my bakery

Agent: I'll help you create a CSRD VSME report. What was your total 
       energy consumption last month?

You: 3200 kWh in Flensburg

Agent: [Calculates emissions: 1.34 tonnes CO2e]
       [Generates VSME snapshot PDF]
       [Creates compliance pack with system card]
       
       Your report is ready! Download: [link]
       Would you like me to email this to you?
```

## Project Structure

```
green-sme-compliance-copilot/
├── main.py                 # FastAPI application
├── models.py               # Pydantic data models
├── utils.py                # ESG calculations, LLM ops
├── pdf_processor.py        # PDF generation & OCR
├── db_init.py              # Database initialization
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── setup.sh                # Automated setup script
├── run.sh                  # Quick start script
├── test_endpoints.sh       # API test suite
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-service orchestration
│
├── config/
│   ├── workflows.yaml           # Workflow recipes
│   ├── compliance_matrix.yaml   # Regulatory mappings
│   ├── n8n_workflow_email.json  # Email automation
│   └── openwebui_config.md      # Chat integration guide
│
├── templates/              # Compliance form templates (PDFs)
├── outputs/                # Generated documents
├── temp/                   # Temporary processing files
└── data/                   # Database and embeddings

Documentation:
├── README.md               # This file
├── HACKATHON_GUIDE.md      # 3-hour build guide
└── desc.txt                # Project description
```

## API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/tools/detectIntent` | POST | Extract intent and entities |
| `/tools/selectWorkflow` | POST | Get workflow recipe |
| `/tools/mapFields` | POST | Semantic form field mapping |
| `/tools/estimateEmissions` | POST | Calculate CO2 from energy |
| `/tools/fillPdf` | POST | Generate compliance document |
| `/tools/generateCompliancePack` | POST | Create full compliance bundle |
| `/tools/emailFile` | POST | Send document via email |
| `/tools/downloadFile/{doc_id}` | GET | Download generated file |

### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools/getWeatherInsight` | POST | Weather data for optimization |
| `/tools/suggestLoadShift` | POST | Energy load-shifting advice |
| `/user/{user_id}` | GET | Fetch user profile |
| `/submissions/{user_id}` | GET | Get submission history |

Full interactive documentation: http://localhost:8000/docs

## Supported Workflows

### 1. CSRD Energy Audit (energyAuditForCSRD)

**Forms**: VSME Snapshot, Disclosure Letter  
**Time**: 15-20 minutes  
**Outputs**: 
- VSME sustainability report (PDF)
- Emissions calculation breakdown
- Load-shifting recommendations
- Compliance pack with system card

**Steps**:
1. Collect energy data (kWh)
2. Calculate Scope 2 emissions
3. Fetch weather insights
4. Generate optimization recommendations
5. Fill VSME form
6. Create compliance documentation
7. Email delivery

### 2. GDPR Article 30 Export (gdprArt30Export)

**Forms**: GDPR Article 30 Record  
**Time**: 10-15 minutes  
**Outputs**:
- Record of Processing Activities (PDF)
- Legal basis mapping
- GDPR compliance pack

**Steps**:
1. Collect processing details
2. Map legal bases
3. Fill Article 30 template
4. Generate compliance documentation
5. Email delivery

### 3. EU AI Act Risk Assessment (euAiActRisk)

**Forms**: EU AI Act Risk Assessment  
**Time**: 20-25 minutes  
**Outputs**:
- Risk classification document (PDF)
- AI system transparency card
- Technical documentation pack

**Steps**:
1. Collect AI system details
2. Classify risk category (Annex III)
3. Check prohibited practices
4. Fill risk assessment form
5. Generate system card
6. Email delivery

## Technical Details

### ML & Embeddings

- **Model**: `intfloat/multilingual-e5-large`
- **Dimension**: 1024
- **Vector Search**: FAISS (Facebook AI Similarity Search)
- **Use Cases**: Form field mapping, semantic similarity

### PDF Processing

- **OCR**: Tesseract 5.x (multilingual support)
- **Generation**: ReportLab (programmatic PDF creation)
- **Parsing**: PyPDF, pdfminer.six

### Emissions Calculation

- **Grid Factor**: 0.42 kg CO2/kWh (Germany default, configurable)
- **Scopes**: Scope 2 (mandatory), Scope 3 (optional)
- **Standards**: GHG Protocol, ESRS E1

### Weather Integration

- **Provider**: OpenWeatherMap API
- **Metrics**: Cloud cover, temperature, solar potential
- **Use Cases**: Load-shifting optimization, solar recommendations

## Compliance Matrix

The system maps features to regulatory requirements:

| Regulation | Articles | Features | Evidence |
|------------|----------|----------|----------|
| GDPR | Art. 30, 32 | User profiles, audit logs | art30_record.pdf |
| CSRD VSME | E1 | Energy tracking, emissions | vsme_snapshot.pdf |
| EU AI Act | Art. 13, 52 | System cards, transparency logs | system_card.pdf |
| ESRS E1 | E1-5, E1-6 | Energy mix, GHG inventory | ghg_inventory.json |

See `config/compliance_matrix.yaml` for complete mappings.

## Development

### Adding a New Workflow

1. Define recipe in `config/workflows.yaml`:

```yaml
my_new_workflow:
  id: my_workflow
  intent: myIntent
  forms: [form_id]
  steps:
    - name: step1
      tool: detectIntent
```

2. Add intent type to `models.py`:

```python
class IntentType(str, Enum):
    MY_INTENT = "myIntent"
```

3. Update intent detection in `utils.py`:

```python
if 'keyword' in text_lower:
    intent_type = IntentType.MY_INTENT
```

4. Create PDF template in `pdf_processor.py`

### Adding a New Form Template

1. Download official form PDF to `/templates`
2. Parse structure: `python -c "from pdf_processor import parse_pdf_form; print(parse_pdf_form('templates/form.pdf'))"`
3. Create filling logic in `pdf_processor.py`
4. Test: `curl -X POST localhost:8000/tools/fillPdf -d '{"formId": "new_form", ...}'`

### Testing

```bash
# Run all endpoint tests
./test_endpoints.sh

# Test specific endpoint
curl -X POST localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "test input"}'

# Check generated files
ls -lh outputs/

# View database
sqlite3 db.sqlite "SELECT * FROM Submission;"
```

## Deployment

### Docker (Recommended)

```bash
docker-compose up -d
```

This deploys all services with proper networking and persistence.

### Cloud Deployment

#### AWS Lambda

1. Package dependencies: `pip install -t package/ -r requirements.txt`
2. Use Mangum adapter for FastAPI
3. Deploy via SAM or Serverless Framework

#### Google Cloud Run

```bash
gcloud run deploy green-sme-copilot \
  --source . \
  --port 8000 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
az container create \
  --resource-group green-sme \
  --name copilot-api \
  --image <your-registry>/green-sme:latest \
  --ports 8000
```

## Hackathon Usage

For OPEN Agentathon participants:

1. **Pre-event** (Nov 16): Run `./setup.sh`, download templates, get API keys
2. **Event day** (Nov 17): Follow `HACKATHON_GUIDE.md` for 3-hour build
3. **Demo**: Use `test_endpoints.sh` to showcase workflows

**Judging Criteria Alignment**:
- **Innovation**: Semantic form mapping, regulation-agnostic design
- **Technical**: ML embeddings, vector search, multi-step orchestration
- **Impact**: Saves SMEs 10+ hours per compliance task
- **Completeness**: 3 full workflows, EU AI Act transparency built-in

## Roadmap

### v0.2 (Post-Hackathon)

- [ ] DPIA (Data Protection Impact Assessment) workflow
- [ ] Multi-language UI (German, French, Spanish)
- [ ] Real-time regulation updates via EU API feeds
- [ ] Evidence folder auto-generation with versioning
- [ ] Advanced semantic search with cross-form intelligence

### v0.3 (Production)

- [ ] ERP integrations (SAP, DATEV, Lexoffice)
- [ ] Mobile app for on-site energy audits
- [ ] Collaborative workflows with approval chains
- [ ] Blockchain-anchored audit trails
- [ ] Machine learning for personalized recommendations

## Contributing

We welcome contributions! Areas of interest:

- New compliance workflows (DPIA, ISO certifications)
- Additional language support
- Form template library expansion
- Integration connectors (Zapier, Make.com)
- Test coverage improvements

## License

MIT License - see LICENSE file

## Support

- **Documentation**: This README + `HACKATHON_GUIDE.md`
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Contact**: team@greensme.ai (for hackathon questions)

## Acknowledgments

Built for OPEN Agentathon (Nov 17, 2025)

**Technologies**:
- FastAPI - Web framework
- sentence-transformers - Embeddings
- FAISS - Vector search
- Tesseract - OCR
- ReportLab - PDF generation
- n8n - Workflow automation
- OpenWebUI - Chat interface

**Regulations**:
- EU CSRD (Corporate Sustainability Reporting Directive)
- GDPR (General Data Protection Regulation)
- EU AI Act (Artificial Intelligence Act)
- ESRS (European Sustainability Reporting Standards)

## Citation

If you use this project in research or production, please cite:

```bibtex
@software{green_sme_copilot_2025,
  title = {Green SME Compliance Co-Pilot},
  author = {Green SME Team},
  year = {2025},
  url = {https://github.com/your-repo/green-sme-compliance-copilot}
}
```

---

**Ready for the hackathon? Start with: `./setup.sh` then read `HACKATHON_GUIDE.md`**

Built with care for SMEs navigating the complexity of EU regulations.
