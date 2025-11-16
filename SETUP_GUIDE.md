# Setup Guide for Green SME Compliance Co-Pilot

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python3.12 -m venv green-agent-env
source green-agent-env/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Tesseract OCR (system dependency)
# Ubuntu/Debian:
sudo apt install tesseract-ocr

# macOS:
brew install tesseract
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenWeather API key (optional but recommended)
# Get free key at: https://openweathermap.org/api
```

### 3. Initialize Database

```bash
python db_init.py
```

### 4. Start Server

```bash
# Option 1: Use startup script
./start.sh

# Option 2: Manual start
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test API

In another terminal:

```bash
python test_api.py
```

Or test manually:

```bash
curl http://localhost:8000/health
```

## Manual Template Downloads

Before using form filling features, download templates to `templates/` directory:

1. **CSRD VSME Standard**
   - URL: https://www.efrag.org/sites/default/files/sites/webpublishing/SiteAssets/VSME%20Standard.pdf
   - Save as: `templates/vsme_snapshot.pdf`

2. **GDPR Article 30 Template**
   - Create a simple template with fields: controller name, address, processing purposes, data categories, recipients, retention periods
   - Save as: `templates/gdpr_art30_record.pdf`

3. **EU AI Act Risk Worksheet**
   - Download from: https://artificialintelligenceact.eu
   - Save as: `templates/ai_act_risk_worksheet.pdf`

## Ingesting Templates (Optional)

To enable semantic form field mapping:

```bash
python ingest.py templates/vsme_snapshot.pdf vsme_snapshot "CSRD VSME Snapshot"
python ingest.py templates/gdpr_art30_record.pdf gdpr_art30 "GDPR Article 30"
python ingest.py templates/ai_act_risk_worksheet.pdf ai_act_risk "EU AI Act Risk"
```

## Optional Services Setup

### OpenWebUI (Chat Interface)

```bash
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

Access at: http://localhost:3000

### n8n (Workflow Automation)

```bash
npm install -g n8n
n8n start
```

Access at: http://localhost:5678

Create webhook workflow:
1. Add Webhook node
2. Add Email node (SMTP)
3. Connect nodes
4. Copy webhook URL to `.env` as `N8N_WEBHOOK_URL`

### MinIO (Object Storage)

```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  --name minio \
  minio/minio server /data --console-address ":9001"
```

Access console at: http://localhost:9001
Default credentials: minioadmin / minioadmin

## Troubleshooting

### Issue: Tesseract not found

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

### Issue: Embedding model download fails

**Solution:**
- Ensure stable internet connection (model is ~1.3GB)
- First run will take time to download
- Model is cached for subsequent runs

### Issue: Database locked

**Solution:**
- Ensure only one process accesses database
- Close any database viewers
- Restart the application

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use different port
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## Next Steps

1. Test API endpoints using `test_api.py`
2. Try example workflows from README
3. Integrate with OpenWebUI for chat interface
4. Set up n8n workflows for email automation
5. Add your own form templates

## Event Day Checklist

- [ ] All dependencies installed
- [ ] Database initialized
- [ ] API server running
- [ ] Templates downloaded (if using form filling)
- [ ] API keys configured (optional)
- [ ] Test script passes
- [ ] OpenWebUI running (optional)
- [ ] n8n configured (optional)

## Support

For issues during the event:
1. Check logs in terminal
2. Verify all services are running
3. Test individual endpoints
4. Check database exists and is accessible
5. Verify environment variables are set
