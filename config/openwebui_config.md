# OpenWebUI Configuration for Green SME Compliance Co-Pilot

## Overview
This document describes how to integrate the Green SME Compliance Co-Pilot with OpenWebUI for a chat interface.

## Setup Steps

### 1. Start OpenWebUI
```bash
docker run -d -p 3000:8080 \
  --name green-sme-openwebui \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

Access at: http://localhost:3000

### 2. Configure FastAPI Backend

In OpenWebUI Settings:
- Navigate to Settings > Connections
- Add Custom API Endpoint: `http://host.docker.internal:8000`
- Enable OpenAI API compatibility mode (optional)

### 3. Create System Prompt

Add this system prompt in OpenWebUI:

```
You are the Green SME Compliance Co-Pilot, an AI assistant that helps small and medium enterprises with sustainability reporting and regulatory compliance.

Your capabilities include:
- CSRD/VSME sustainability reporting
- GDPR Article 30 record generation
- EU AI Act risk assessment
- Energy audit and emissions calculation
- Load-shifting recommendations

You have access to the following tools via API endpoints:

1. /tools/detectIntent - Understand user requests
2. /tools/estimateEmissions - Calculate CO2 emissions
3. /tools/fillPdf - Generate compliance documents
4. /tools/emailFile - Send documents to users

IMPORTANT TRANSPARENCY NOTICE:
- Always inform users they are interacting with an AI system
- Explain your reasoning and data sources
- Allow users to review and approve all generated documents
- Flag when professional legal review is recommended

When a user asks for compliance help:
1. Detect their intent
2. Gather required information
3. Execute the appropriate workflow
4. Generate and deliver documents
5. Log all actions for audit trail

Be professional, clear, and proactive. Help SMEs navigate complex regulations with confidence.
```

### 4. Configure Tools/Functions

Add function definitions for tool calling:

```json
{
  "functions": [
    {
      "name": "detectIntent",
      "description": "Detect user intent and extract information from natural language",
      "parameters": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string",
            "description": "User's input text"
          }
        },
        "required": ["text"]
      }
    },
    {
      "name": "estimateEmissions",
      "description": "Calculate CO2 emissions from energy consumption",
      "parameters": {
        "type": "object",
        "properties": {
          "kWh": {
            "type": "number",
            "description": "Energy consumption in kWh"
          },
          "gridFactor": {
            "type": "number",
            "description": "Grid emission factor (default 0.42 for Germany)"
          }
        },
        "required": ["kWh"]
      }
    },
    {
      "name": "generateComplianceDocument",
      "description": "Generate compliance documentation (CSRD, GDPR, AI Act)",
      "parameters": {
        "type": "object",
        "properties": {
          "formId": {
            "type": "string",
            "description": "Form type: vsme_snapshot, gdpr_art30, eu_ai_act_risk"
          },
          "fieldValues": {
            "type": "object",
            "description": "Field values for the form"
          }
        },
        "required": ["formId", "fieldValues"]
      }
    }
  ]
}
```

### 5. Example Conversations

#### CSRD Energy Audit
```
User: I need help with a CSRD energy audit. We used 3200 kWh last month in Flensburg.

Agent: I'll help you create a CSRD VSME sustainability report. Let me gather the information:

1. Detecting intent... [calls detectIntent API]
2. Calculating emissions... [calls estimateEmissions with kWh=3200]
3. Getting weather insights for optimization... [calls getWeatherInsight for Flensburg]
4. Generating VSME snapshot... [calls fillPdf with vsme_snapshot template]

Your emissions: 1.34 tonnes CO2e
Report generated: filled_vsme_snapshot_20241116.pdf
Download: http://localhost:8000/tools/downloadFile/filled_vsme_snapshot_20241116.pdf

Would you like me to email this to you?
```

#### GDPR Article 30
```
User: Generate a GDPR Article 30 record for my bakery.

Agent: I'll create your GDPR Article 30 Record of Processing Activities. I need some information:

1. What are your main data processing purposes?
2. What categories of personal data do you process?
3. Who are the recipients of this data?

[User provides answers via chat]

Generating your Article 30 record...
Document ready: filled_gdpr_art30_20241116.pdf

This includes your controller details, processing purposes, data categories, and security measures.
```

## 6. API Integration

### Method 1: Direct HTTP Calls
OpenWebUI can make direct HTTP calls to FastAPI endpoints:

```javascript
// In OpenWebUI custom function
async function callComplianceAPI(endpoint, data) {
  const response = await fetch(`http://host.docker.internal:8000${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return await response.json();
}
```

### Method 2: OpenWebUI Pipelines
Create a pipeline in OpenWebUI that routes to FastAPI:

```python
# pipeline.py in OpenWebUI
from typing import Dict, Any

class Pipeline:
    def __init__(self):
        self.name = "Green SME Compliance"
        self.base_url = "http://localhost:8000"
    
    async def on_message(self, message: str, context: Dict[str, Any]):
        # Route to appropriate endpoint based on intent
        import requests
        
        intent_resp = requests.post(
            f"{self.base_url}/tools/detectIntent",
            json={"text": message}
        ).json()
        
        # Execute workflow based on intent
        # Return formatted response
        return formatted_response
```

## 7. Transparency & EU AI Act Compliance

Always display this disclaimer in OpenWebUI:

```
This is an AI-powered system (Green SME Compliance Co-Pilot) designed to assist with compliance documentation. 
All generated documents should be reviewed by qualified personnel before submission to authorities. 
The system maintains audit logs and complies with EU AI Act transparency requirements.
```

## 8. Troubleshooting

### Connection Issues
- Check FastAPI is running: `curl http://localhost:8000`
- Use `host.docker.internal` not `localhost` from Docker
- Verify firewall allows port 8000

### Tool Calling Not Working
- Ensure OpenAI function calling format is used
- Check FastAPI logs for errors
- Test endpoints directly with curl/Postman first

## 9. Demo Scenario for Hackathon

1. User opens OpenWebUI at localhost:3000
2. Sends: "I need to report our energy usage for CSRD"
3. Agent detects intent, asks for kWh value
4. User: "We used 3200 kWh in October in Flensburg"
5. Agent calculates emissions, generates PDF, offers email delivery
6. User approves, receives compliance pack via email
7. Total time: < 3 minutes

This demonstrates:
- Natural language understanding
- Multi-step workflow orchestration
- Document generation
- Regulatory compliance
- User control and transparency