# Green SME Compliance Co-Pilot - Hackathon Guide
## OPEN Agentathon (Nov 17, 2025) - Quick Start

This guide gets you from zero to demo in under 3 hours for the hackathon working session.

## Pre-Event Preparation (Nov 16 - Today)

### 1. Event Registration
Register at: https://cloud.ai2e.de/index.php/apps/forms/s/BL8jndcGfjNyXzHbCBbbKpfY

Use case description:
```
Green SME Compliance Co-Pilot: AI agent that automates ESG audits and CSRD/GDPR 
compliance filings for SMEs using semantic form mapping and regulatory reasoning.
```

### 2. System Setup (30 minutes)

```bash
git clone <your-repo>
cd green-sme-compliance-copilot

chmod +x setup.sh run.sh
./setup.sh
```

This installs:
- Python dependencies
- SQLite database with mock data
- Directory structure
- Environment configuration

### 3. Download Templates (15 minutes)

Required forms for MVP:

1. CSRD VSME Standard
   - URL: https://www.efrag.org/sites/default/files/sites/webpublishing/SiteAssets/VSME%20Standard.pdf
   - Save to: `/templates/vsme_standard.pdf`

2. BAFA Energy Audit Guidelines
   - URL: https://www.bafa.de/SharedDocs/Downloads/EN/Energy/ea_guidelines.pdf?__blob=publicationFile&v=1
   - Save to: `/templates/energy_audit_bafa.pdf`

3. Create GDPR Art 30 Template (no official form exists)
   - Use the system to generate a blank template

### 4. Configure API Keys

Edit `.env`:

```bash
OPENWEATHER_API_KEY=your_key_here
MISTRAL_API_KEY=optional_for_enhanced_nlp
```

Get OpenWeather key (free): https://openweathermap.org/api

### 5. Test Installation

```bash
source green-agent-env/bin/activate
python db_init.py
python main.py
```

Visit: http://localhost:8000/docs

Test endpoint: GET http://localhost:8000/

Expected response:
```json
{
  "status": "running",
  "service": "Green SME Compliance Co-Pilot",
  "version": "0.1.0",
  "models_loaded": true
}
```

## Event Day (Nov 17) - 3-Hour Build

### Hour 1: Core Workflow (60 mins)

#### Test Intent Detection
```bash
curl -X POST http://localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "I need help with energy audit for CSRD. We used 3200 kWh in Flensburg"}'
```

Expected response:
```json
{
  "intentType": "energyAuditForCSRD",
  "slots": {
    "kWh": 3200,
    "city": "Flensburg"
  },
  "confidence": 0.85
}
```

#### Test Emissions Calculation
```bash
curl -X POST http://localhost:8000/tools/estimateEmissions \
  -H "Content-Type: application/json" \
  -d '{"kWh": 3200, "gridFactor": 0.42}'
```

#### Test PDF Generation
```bash
curl -X POST http://localhost:8000/tools/fillPdf \
  -H "Content-Type: application/json" \
  -d '{
    "formId": "vsme_snapshot",
    "fieldValues": {
      "name": "Prime Bakery GmbH",
      "address": "Flensburger Strasse 1",
      "city": "Flensburg",
      "postal_code": "24937",
      "kWh": 3200,
      "tCO2e": 1.34
    }
  }'
```

Check output in `/outputs` directory.

### Hour 2: Integration & Automation (60 mins)

#### Setup n8n (Optional)
```bash
npx n8n
```

Import workflow: `/config/n8n_workflow_email.json`

Configure SMTP credentials in n8n.

#### OR Mock Email Delivery
The system automatically mocks email sending if n8n is not configured.

#### Test Complete Flow
```bash
# Full workflow test
curl -X POST http://localhost:8000/tools/selectWorkflow \
  -H "Content-Type: application/json" \
  -d '{
    "intentType": "energyAuditForCSRD",
    "slots": {"kWh": 3200, "city": "Flensburg"},
    "userId": 1
  }'
```

#### Test Compliance Pack Generation
```bash
curl -X POST http://localhost:8000/tools/generateCompliancePack \
  -H "Content-Type: application/json" \
  -d '{
    "submissionId": 1,
    "regulations": ["CSRD", "VSME", "EU_AI_Act"]
  }'
```

### Hour 3: Demo Polish & Testing (60 mins)

#### Setup OpenWebUI (Optional Chat Interface)
```bash
docker run -d -p 3000:8080 \
  --name openwebui \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

Configure system prompt from `/config/openwebui_config.md`

#### Create Demo Scenario

Test the "Prime Bakery" scenario:

1. User: "I'm Prime Bakery in Flensburg, need CSRD energy audit"
2. System detects intent
3. User provides: "3200 kWh last month"
4. System calculates emissions (1.34 tonnes)
5. System generates VSME snapshot PDF
6. System creates compliance pack with EU AI Act system card
7. System offers email delivery

Total flow: < 5 minutes

#### Prepare Pitch (15 mins)

Key points:
- Problem: SMEs overwhelmed by compliance (CSRD, GDPR, AI Act)
- Solution: Semantic form mapping + automated workflows
- Scalable: Drop any form, agent learns structure
- Transparent: EU AI Act compliant with system cards
- Proven: Works with 3 regulations, 5+ forms

#### Test Edge Cases

1. Missing data: System asks questions
2. Low confidence mapping: Flags for review
3. Multiple forms: Bundles into compliance pack
4. Weather integration: Load shift recommendations

## Common Issues & Fixes

### Models Not Loading
```bash
pip install --upgrade sentence-transformers torch
```

### PDF Generation Fails
Check ReportLab:
```bash
pip install --upgrade reportlab
```

### OCR Not Working
Install Tesseract:
```bash
# Ubuntu
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Database Errors
Reinitialize:
```bash
rm db.sqlite
python db_init.py
```

## Demo Script for Judges

```
"We built Green SME Compliance Co-Pilot - an AI agent that automates 
compliance for small businesses.

[Open browser to localhost:8000/docs]

Here's our agent handling a real CSRD energy audit:

[POST to /tools/detectIntent with bakery example]

It understands natural language, extracts data, calculates emissions 
using real weather APIs for optimization...

[Show emissions calculation result]

...and generates compliant documents automatically.

[Show generated PDF in /outputs]

The key innovation: semantic form mapping. We can drop ANY compliance form, 
and the agent learns its structure using embeddings and vector search.

[Show FAISS index, embedding model]

It's also EU AI Act compliant - every submission includes a transparency 
system card documenting what the AI does.

[Show compliance pack PDF with system card]

We've implemented 3 full workflows: CSRD, GDPR Article 30, and EU AI Act 
risk assessment. Each takes under 5 minutes vs. hours of manual work.

Built with FastAPI, sentence transformers, FAISS, and Tesseract OCR. 
Scales to any SME, any regulation.

Questions?"
```

## Post-Event: Extensions

After hackathon, add:
1. DPIA (Data Protection Impact Assessment) workflow
2. Evidence folder auto-generation
3. Multi-language support (already partially there with multilingual-e5)
4. Real-time regulation updates via API
5. Integration with ERP systems
6. Mobile app for on-site audits

## Resources

- API Documentation: http://localhost:8000/docs
- Workflow Recipes: `/config/workflows.yaml`
- Compliance Matrix: `/config/compliance_matrix.yaml`
- OpenWebUI Config: `/config/openwebui_config.md`
- n8n Workflow: `/config/n8n_workflow_email.json`

## Support During Event

If stuck:
1. Check logs: `tail -f *.log`
2. Test individual endpoints
3. Use mock data from database
4. Fallback to manual mapping if ML fails
5. Ask mentors

## Success Criteria

By end of 3 hours, demonstrate:
- [x] Intent detection from natural language
- [x] Automated emissions calculation
- [x] PDF document generation
- [x] Compliance pack with system card
- [x] At least 1 complete workflow (CSRD)
- [x] EU AI Act transparency compliance

## Judging Criteria Alignment

1. Innovation: Semantic form mapping, regulation-agnostic
2. Technical: FastAPI + ML embeddings + vector search
3. Impact: Saves SMEs hours per compliance task
4. Scalability: Works with any form, any regulation
5. Completeness: Full workflows, not just POC

Good luck at the hackathon!