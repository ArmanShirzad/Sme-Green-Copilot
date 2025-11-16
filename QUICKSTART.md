# Quick Start Guide - Hackathon Day

## Pre-Event Checklist (Today, Nov 16)

- [ ] Register for event: https://cloud.ai2e.de/index.php/apps/forms/s/BL8jndcGfjNyXzHbCBbbKpfY
- [ ] Download form templates (see templates/README.md)
- [ ] Get OpenWeather API key (free): https://openweathermap.org/api
- [ ] Test Tesseract installation: `tesseract --version`
- [ ] Clone repo and run `./setup.sh`

## 3-Hour Build Plan

### Hour 1: Core Setup (60 mins)

1. **Environment Setup** (10 mins)
   ```bash
   ./setup.sh
   cp .env.example .env
   # Add OPENWEATHER_API_KEY to .env
   ```

2. **Database Init** (5 mins)
   ```bash
   python db_init.py
   ```

3. **Start API Server** (5 mins)
   ```bash
   source green-agent-env/bin/activate
   uvicorn main:app --reload
   ```

4. **Test Core Endpoints** (20 mins)
   ```bash
   python test_api.py
   ```

5. **Ingest Form Templates** (20 mins)
   ```bash
   # If you have templates downloaded
   python ingest.py templates/vsme_snapshot.pdf vsme_snapshot "CSRD VSME" csrd
   python ingest.py templates/gdpr_art30.pdf gdpr_art30 "GDPR Art.30" gdpr
   ```

### Hour 2: Integration & Testing (60 mins)

1. **Test Workflows** (20 mins)
   ```bash
   python example_usage.py
   ```

2. **OpenWebUI Integration** (20 mins)
   - Start: `docker-compose up -d`
   - Access: http://localhost:3000
   - Configure system prompt (see README.md)
   - Test chat interface

3. **Email Integration** (20 mins)
   - Set up n8n workflow (if time permits)
   - Or use mock email function (already implemented)
   - Test email sending

### Hour 3: Polish & Demo Prep (60 mins)

1. **Edge Case Handling** (20 mins)
   - Test with missing data
   - Test with low confidence mappings
   - Verify error handling

2. **Demo Script** (20 mins)
   - Prepare 3 demo scenarios:
     - CSRD energy audit
     - GDPR Art.30 export
     - EU AI Act risk check
   - Document expected outputs

3. **Final Testing** (20 mins)
   - Run full workflow end-to-end
   - Verify PDF generation
   - Check compliance pack generation
   - Test API documentation at /docs

## Quick Commands Reference

```bash
# Start API
uvicorn main:app --reload

# Test API
python test_api.py

# Run examples
python example_usage.py

# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## Demo Scenarios

### Scenario 1: CSRD Energy Audit
**Input:** "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month in Flensburg."

**Expected Output:**
- Intent: energyAuditForCSRD
- Workflow: csrd_audit
- PDF: filled_vsme_snapshot.pdf
- Compliance pack: compliance_pack_*.pdf
- Emissions: ~1.26 tCO2e

### Scenario 2: GDPR Article 30
**Input:** "Generate a GDPR Article 30 processing record for our data activities."

**Expected Output:**
- Intent: gdprArticle30
- Workflow: gdpr_art30
- PDF: filled_gdpr_art30_record.pdf
- Compliance pack with GDPR Art.30 details

### Scenario 3: EU AI Act Risk Check
**Input:** "Check if our AI system needs EU AI Act compliance."

**Expected Output:**
- Intent: euAIActRisk
- Workflow: ai_act_check
- Risk assessment PDF
- System card generation

## Troubleshooting

**API won't start:**
- Check port 8000 is free: `lsof -i :8000`
- Verify dependencies: `pip list | grep fastapi`

**Models not loading:**
- First run downloads models (~500MB)
- Check internet connection
- Models cached in `~/.cache/huggingface/`

**Database errors:**
- Reinitialize: `python db_init.py`
- Check DB_PATH in .env

**OCR not working:**
- Verify Tesseract: `tesseract --version`
- System falls back to text extraction automatically

## Pitch Points

1. **Problem:** SMEs struggle with complex compliance (CSRD/GDPR/EU AI Act)
2. **Solution:** AI agent automates form filling via semantic mapping
3. **Key Innovation:** Handles form variations without manual mapping
4. **Scalability:** "Drop any form" - semantic embeddings handle variations
5. **Compliance:** Built-in audit trails, system cards, transparency logs
6. **Doability:** Core is FastAPI + local tools, no heavy ML training

## Post-Event Extensions

- Full DPIA via chained prompts
- Evidence folder generation via n8n
- Additional regulations (German Energie Audit, etc.)
- Enhanced OCR with form field detection
- ERP system integrations

## Contact & Support

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Test Scripts: `python test_api.py` or `python example_usage.py`

Good luck with the hackathon!
