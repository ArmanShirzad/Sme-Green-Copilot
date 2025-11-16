# Green SME Compliance Co-Pilot - Quick Start

## 5-Minute Setup

### 1. Install

```bash
./setup.sh
```

This creates virtual environment, installs dependencies, and initializes database.

### 2. Configure

Edit `.env`:
```bash
OPENWEATHER_API_KEY=your_key_here
```

Get free key at: https://openweathermap.org/api

### 3. Run

```bash
./run.sh
```

Server starts at: http://localhost:8000

### 4. Test

```bash
./test_endpoints.sh
```

Or visit: http://localhost:8000/docs

## First API Call

```bash
curl -X POST http://localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "I need CSRD report for 3200 kWh energy consumption in Flensburg"}'
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

## Generate Your First Document

```bash
curl -X POST http://localhost:8000/tools/fillPdf \
  -H "Content-Type: application/json" \
  -d '{
    "formId": "vsme_snapshot",
    "fieldValues": {
      "name": "My Company GmbH",
      "city": "Berlin",
      "kWh": 3200,
      "tCO2e": 1.34
    }
  }'
```

Check `outputs/` directory for generated PDF.

## What Next?

- **Full Guide**: See `README.md`
- **Hackathon**: See `HACKATHON_GUIDE.md`
- **API Reference**: http://localhost:8000/docs
- **Examples**: See `test_endpoints.sh`

## Common Issues

**Models not loading?**
```bash
pip install --upgrade sentence-transformers torch
```

**Port 8000 in use?**
```bash
# Edit .env
APP_PORT=8001
```

**Database errors?**
```bash
rm db.sqlite
python db_init.py
```

## Support

- Documentation: `README.md` (comprehensive)
- API Docs: http://localhost:8000/docs
- Test Script: `./test_endpoints.sh`

**Ready in 5 minutes. Start building!**
