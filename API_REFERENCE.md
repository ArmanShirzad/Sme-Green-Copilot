# API Reference

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "embedding_model": "loaded",
  "faiss_index": "ready"
}
```

---

### Detect Intent

**POST** `/tools/detectIntent`

Detect user intent from chat input.

**Request:**
```json
{
  "text": "I need an energy audit for CSRD compliance"
}
```

**Response:**
```json
{
  "intentType": "energyAuditForCSRD",
  "slots": {
    "kWh": 3000,
    "city": "Flensburg"
  },
  "confidence": 0.94
}
```

**Intent Types:**
- `energyAuditForCSRD` - Energy audit for CSRD compliance
- `gdprArt30` - GDPR Article 30 record generation
- `euAiActRisk` - EU AI Act risk assessment

---

### Select Workflow

**POST** `/tools/selectWorkflow`

Select workflow recipe based on detected intent.

**Request:**
```json
{
  "intentType": "energyAuditForCSRD",
  "slots": {
    "kWh": 3000,
    "city": "Flensburg"
  }
}
```

**Response:**
```json
{
  "recipeId": "csrd_audit",
  "recipeName": "CSRD Energy Audit",
  "neededForms": ["vsme_snapshot", "disclosure_letter"],
  "workflow": [...],
  "questions": []
}
```

---

### Map Fields

**POST** `/tools/mapFields`

Map form fields to user data using semantic similarity.

**Request:**
```json
{
  "labels": ["Company Name:", "Address:", "Energy Consumption (kWh):"],
  "userData": {
    "name": "Prime Bakery",
    "address": "Flensburg St 1, 24937 Flensburg"
  },
  "slots": {
    "kWh": 3000
  }
}
```

**Response:**
```json
{
  "fieldValues": {
    "name": "Prime Bakery",
    "address": "Flensburg St 1, 24937 Flensburg",
    "energy_kwh": 3000,
    "tCO2e": 1.26
  },
  "lowConfidence": []
}
```

---

### Estimate Emissions

**POST** `/tools/estimateEmissions`

Calculate CO2 emissions from energy consumption.

**Request:**
```json
{
  "kWh": 3000,
  "gridFactor": 0.42,
  "country": "DE"
}
```

**Response:**
```json
{
  "tCO2e": 1.26,
  "kWh": 3000,
  "gridFactor": 0.42,
  "country": "DE",
  "note": "Estimated with DE grid factor"
}
```

**Supported Countries:**
- `DE` - Germany (default: 0.42 kg CO2/kWh)
- `FR` - France (0.056 kg CO2/kWh)
- `PL` - Poland (0.724 kg CO2/kWh)
- `ES` - Spain (0.25 kg CO2/kWh)

---

### Fill PDF

**POST** `/tools/fillPdf`

Fill PDF form with field values.

**Request:**
```json
{
  "formId": "vsme_snapshot",
  "fieldValues": {
    "name": "Prime Bakery",
    "energy_kwh": 3000,
    "tCO2e": 1.26
  }
}
```

**Response:**
```json
{
  "docId": "outputs/filled_vsme_snapshot_20241116_143022.pdf",
  "formId": "vsme_snapshot",
  "status": "filled"
}
```

---

### Parse Form

**POST** `/tools/parseForm`

Extract form field labels from PDF.

**Request:**
```json
{
  "pdfPath": "templates/vsme_snapshot.pdf"
}
```

**Response:**
```json
{
  "labels": ["Company Name:", "Address:", "Energy Consumption:"],
  "textContent": "Full extracted text...",
  "pageCount": 1
}
```

---

### Collect Answers

**POST** `/tools/collectAnswers`

Collect answers to questions (mock for MVP).

**Request:**
```json
{
  "questions": ["What is your monthly energy consumption in kWh?"],
  "submissionId": 1
}
```

**Response:**
```json
{
  "answers": {
    "What is your monthly energy consumption in kWh?": "3000"
  },
  "status": "collected"
}
```

---

### Export File

**POST** `/tools/exportFile`

Export file to storage (MinIO or local).

**Request:**
```json
{
  "filePath": "outputs/filled_vsme_snapshot_20241116_143022.pdf"
}
```

**Response:**
```json
{
  "fileUrl": "/outputs/filled_vsme_snapshot_20241116_143022.pdf",
  "filePath": "outputs/filled_vsme_snapshot_20241116_143022.pdf",
  "status": "exported"
}
```

---

### Email File

**POST** `/tools/emailFile`

Send file via email using n8n webhook.

**Request:**
```json
{
  "filePath": "outputs/compliance_pack_1.pdf",
  "recipient": "info@bakery.de"
}
```

**Response:**
```json
{
  "status": "sent",
  "recipient": "info@bakery.de",
  "filePath": "outputs/compliance_pack_1.pdf",
  "n8nResponse": 200
}
```

---

### Generate Compliance Pack

**POST** `/tools/generateCompliancePack`

Generate compliance pack PDF with regulatory mappings.

**Request:**
```json
{
  "submissionId": 1,
  "recipeId": "csrd_audit",
  "regulations": ["CSRD", "ESRS E1"]
}
```

**Response:**
```json
{
  "filePath": "outputs/compliance_pack_1.pdf",
  "submissionId": 1,
  "regulations": ["CSRD", "ESRS E1"],
  "status": "generated"
}
```

---

### Classify AI Risk

**POST** `/tools/classifyAIRisk`

Classify AI system risk level per EU AI Act.

**Request:**
```json
{
  "description": "Biometric identification system for employee access"
}
```

**Response:**
```json
{
  "risk_level": "high",
  "reason": "Matches high-risk categories: biometric, identification, recognition",
  "requires_annex_iii": true,
  "compliance_requirements": [
    "Risk assessment",
    "System card",
    "Transparency log"
  ]
}
```

---

## Example Workflow

### Complete CSRD Energy Audit Flow

```bash
# 1. Detect intent
curl -X POST http://localhost:8000/tools/detectIntent \
  -H "Content-Type: application/json" \
  -d '{"text": "I need an energy audit for CSRD, we use 3000 kWh per month in Flensburg"}'

# 2. Select workflow
curl -X POST http://localhost:8000/tools/selectWorkflow \
  -H "Content-Type: application/json" \
  -d '{"intentType": "energyAuditForCSRD", "slots": {"kWh": 3000, "city": "Flensburg"}}'

# 3. Estimate emissions
curl -X POST http://localhost:8000/tools/estimateEmissions \
  -H "Content-Type: application/json" \
  -d '{"kWh": 3000, "country": "DE"}'

# 4. Fill PDF form
curl -X POST http://localhost:8000/tools/fillPdf \
  -H "Content-Type: application/json" \
  -d '{"formId": "vsme_snapshot", "fieldValues": {"name": "Prime Bakery", "energy_kwh": 3000, "tCO2e": 1.26}}'

# 5. Generate compliance pack
curl -X POST http://localhost:8000/tools/generateCompliancePack \
  -H "Content-Type: application/json" \
  -d '{"submissionId": 1, "recipeId": "csrd_audit"}'

# 6. Email file
curl -X POST http://localhost:8000/tools/emailFile \
  -H "Content-Type: application/json" \
  -d '{"filePath": "outputs/compliance_pack_1.pdf", "recipient": "info@bakery.de"}'
```

## Error Responses

All endpoints may return errors in this format:

```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request (missing/invalid parameters)
- `404` - Not Found (file/resource not found)
- `500` - Internal Server Error
