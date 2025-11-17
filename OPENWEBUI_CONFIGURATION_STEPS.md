# OpenWebUI Configuration Steps

This guide provides step-by-step instructions for configuring OpenWebUI to work with the Green SME Compliance Co-Pilot FastAPI backend.

## Overview

OpenWebUI serves as the chat interface layer that connects users to the compliance co-pilot backend. It provides a conversational interface where users can interact with the system using natural language, and the system will automatically detect intents, select workflows, and execute compliance tasks.

## Prerequisites

- Docker installed and running
- FastAPI backend running on port 8000
- OpenWebUI Docker image access
- API endpoints accessible from OpenWebUI container

## Step 1: Start OpenWebUI Container

Run OpenWebUI using Docker:

```bash
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e ENABLE_SIGNUP=false \
  -e DEFAULT_USER_ROLE=admin \
  --name open-webui \
  --restart unless-stopped \
  ghcr.io/open-webui/open-webui:main
```

**Note:** The container maps port 8080 (internal) to 3000 (host). Access OpenWebUI at `http://localhost:3000`

## Step 2: Configure OpenWebUI Settings

### 2.1 Access OpenWebUI

1. Open browser and navigate to `http://localhost:3000`
2. Create an admin account (first user is automatically admin)
3. Log in with your admin credentials

### 2.2 Configure API Connection

1. Navigate to **Settings** (gear icon in top right)
2. Go to **Connections** or **External APIs** section
3. Add a new connection with the following settings:
   - **Name:** Green Compliance Co-Pilot
   - **Base URL:** `http://host.docker.internal:8000` (if OpenWebUI is in Docker) or `http://localhost:8000` (if running on host)
   - **Type:** Custom API / Function Calling

### 2.3 Configure Function Calling

OpenWebUI supports function calling (tools) that can connect to your FastAPI endpoints. Configure the following:

1. Go to **Settings** > **Functions** or **Tools**
2. Enable **Function Calling** or **Tool Calling**
3. Add the following function definitions:

```json
{
  "functions": [
    {
      "name": "detectIntent",
      "description": "Detect user intent from chat input for compliance tasks (CSRD, GDPR, EU AI Act)",
      "parameters": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string",
            "description": "User's chat message or query"
          }
        },
        "required": ["text"]
      },
      "endpoint": "http://host.docker.internal:8000/tools/detectIntent"
    },
    {
      "name": "selectWorkflow",
      "description": "Select appropriate workflow recipe based on detected intent",
      "parameters": {
        "type": "object",
        "properties": {
          "intentType": {
            "type": "string",
            "description": "Detected intent type (e.g., energyAuditForCSRD, gdprArt30, euAiActRisk)"
          },
          "slots": {
            "type": "object",
            "description": "Extracted slots/entities from user input"
          }
        },
        "required": ["intentType", "slots"]
      },
      "endpoint": "http://host.docker.internal:8000/tools/selectWorkflow"
    },
    {
      "name": "estimateEmissions",
      "description": "Estimate CO2 emissions from energy consumption in kWh",
      "parameters": {
        "type": "object",
        "properties": {
          "kWh": {
            "type": "number",
            "description": "Energy consumption in kilowatt-hours"
          },
          "country": {
            "type": "string",
            "description": "Country code (default: DE)",
            "default": "DE"
          },
          "gridFactor": {
            "type": "number",
            "description": "Optional grid emission factor"
          }
        },
        "required": ["kWh"]
      },
      "endpoint": "http://host.docker.internal:8000/tools/estimateEmissions"
    },
    {
      "name": "generateCompliancePack",
      "description": "Generate compliance pack PDF with regulatory mappings",
      "parameters": {
        "type": "object",
        "properties": {
          "submissionId": {
            "type": "integer",
            "description": "Submission ID for tracking"
          },
          "recipeId": {
            "type": "string",
            "description": "Recipe ID (e.g., csrd_audit, gdpr_art30, eu_ai_act_risk)"
          },
          "regulations": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of regulations to include"
          }
        },
        "required": ["submissionId", "recipeId"]
      },
      "endpoint": "http://host.docker.internal:8000/tools/generateCompliancePack"
    },
    {
      "name": "classifyAIRisk",
      "description": "Classify AI system risk level per EU AI Act requirements",
      "parameters": {
        "type": "object",
        "properties": {
          "description": {
            "type": "string",
            "description": "Description of the AI system to assess"
          }
        },
        "required": ["description"]
      },
      "endpoint": "http://host.docker.internal:8000/tools/classifyAIRisk"
    },
    {
      "name": "inferRegulatoryData",
      "description": "Infer regulatory data from description using LLM reasoning",
      "parameters": {
        "type": "object",
        "properties": {
          "description": {
            "type": "string",
            "description": "Description of the system or process"
          },
          "regulation": {
            "type": "string",
            "description": "Regulation type (GDPR, CSRD, EU_AI_ACT)",
            "default": "GDPR"
          }
        },
        "required": ["description"]
      },
      "endpoint": "http://host.docker.internal:8000/tools/inferRegulatoryData"
    }
  ]
}
```

## Step 3: Configure System Prompt

Create a system prompt that instructs the LLM to use the available tools:

1. Go to **Settings** > **Models** or **Prompts**
2. Create or edit the default system prompt:

```
You are the Green SME Compliance Co-Pilot, an AI assistant that helps small and medium enterprises navigate ESG audits and compliance filings.

Your capabilities include:
- CSRD (Corporate Sustainability Reporting Directive) compliance and energy audits
- GDPR Article 30 processing record generation
- EU AI Act risk assessment and classification
- Emissions calculations and environmental impact assessment
- Compliance pack generation with regulatory mappings

When users ask about compliance tasks:
1. Use detectIntent to understand what they need
2. Use selectWorkflow to determine the appropriate workflow
3. Collect any missing information through conversation
4. Use the appropriate tools (estimateEmissions, classifyAIRisk, etc.) to complete tasks
5. Generate compliance packs when ready

Always be helpful, explain regulatory requirements clearly, and guide users through the compliance process step by step.
```

## Step 4: Configure Model Settings

1. Go to **Settings** > **Models**
2. Add or configure a model that supports function calling:
   - **Groq LLaMA 3.1 70B** (recommended for regulatory reasoning)
   - **OpenAI GPT-4** (if available)
   - **Anthropic Claude** (if available)

3. For Groq models, configure:
   - **API Key:** Your GROQ_API_KEY from `.env`
   - **Base URL:** `https://api.groq.com/openai/v1`
   - **Model:** `llama-3.1-70b-versatile` or `llama-3.1-8b-instant`

## Step 5: Test the Integration

### 5.1 Test Intent Detection

Start a new chat and try:

```
I need an energy audit for CSRD compliance
```

The system should:
1. Detect intent: `energyAuditForCSRD`
2. Select workflow: `csrd_audit`
3. Ask for missing information (kWh, city)

### 5.2 Test Emissions Calculation

```
Calculate emissions for 3000 kWh in Germany
```

Should trigger `estimateEmissions` function.

### 5.3 Test AI Risk Classification

```
I have an AI system that processes customer data for fraud detection. What's the risk level?
```

Should trigger `classifyAIRisk` function.

## Step 6: Advanced Configuration

### 6.1 Custom Workflows

You can create custom workflows in OpenWebUI that chain multiple function calls:

1. Go to **Workflows** or **Automations**
2. Create a new workflow:
   - Trigger: User message contains "CSRD audit"
   - Actions:
     1. Call `detectIntent`
     2. Call `selectWorkflow`
     3. Collect missing data
     4. Call `estimateEmissions` (if needed)
     5. Call `generateCompliancePack`

### 6.2 Webhook Integration

If you want OpenWebUI to send results to your backend:

1. Configure webhook in OpenWebUI settings
2. Set webhook URL to: `http://host.docker.internal:8000/webhooks/openwebui`
3. Add webhook handler in `main.py` if needed

### 6.3 Docker Network Configuration

If OpenWebUI cannot reach the FastAPI backend:

1. Create a Docker network:
```bash
docker network create compliance-network
```

2. Connect both containers:
```bash
docker network connect compliance-network open-webui
docker network connect compliance-network <fastapi-container-name>
```

3. Update API URLs to use container names instead of `host.docker.internal`

## Step 7: Troubleshooting

### Issue: OpenWebUI cannot reach FastAPI backend

**Solution:**
- Check if FastAPI is running: `curl http://localhost:8000/health`
- Verify network connectivity from OpenWebUI container:
  ```bash
  docker exec open-webui curl http://host.docker.internal:8000/health
  ```
- Use Docker network if `host.docker.internal` doesn't work

### Issue: Function calls not working

**Solution:**
- Verify function definitions are correctly formatted JSON
- Check that the model supports function calling
- Review OpenWebUI logs: `docker logs open-webui`
- Test API endpoints directly: `curl -X POST http://localhost:8000/tools/detectIntent -H "Content-Type: application/json" -d '{"text":"test"}'`

### Issue: CORS errors

**Solution:**
- Verify CORS is enabled in `main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # Or specific origins
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### Issue: Authentication required

**Solution:**
- If your FastAPI requires authentication, configure API keys in OpenWebUI function settings
- Add headers to function calls:
  ```json
  {
    "headers": {
      "Authorization": "Bearer YOUR_API_KEY"
    }
  }
  ```

## Step 8: Production Considerations

### 8.1 Security

- Disable signup in production: `ENABLE_SIGNUP=false`
- Use environment variables for API keys
- Configure proper CORS origins (not `*`)
- Enable HTTPS for both OpenWebUI and FastAPI

### 8.2 Performance

- Use connection pooling for API calls
- Cache frequently used responses
- Monitor API response times
- Consider rate limiting

### 8.3 Monitoring

- Set up logging for function calls
- Monitor error rates
- Track user interactions
- Set up alerts for API failures

## Quick Reference

**OpenWebUI URL:** `http://localhost:3000`

**FastAPI URL:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

**Health Check:** `http://localhost:8000/health`

**Docker Commands:**
```bash
# Start OpenWebUI
docker start open-webui

# Stop OpenWebUI
docker stop open-webui

# View logs
docker logs -f open-webui

# Restart OpenWebUI
docker restart open-webui
```

## Next Steps

1. Test all three MVP recipes (CSRD, GDPR, EU AI Act)
2. Customize system prompts for your use case
3. Add additional function definitions as needed
4. Configure email notifications via n8n integration
5. Set up monitoring and logging

## Support

For issues:
1. Check FastAPI logs: `tail -f logs/app.log` (if configured)
2. Check OpenWebUI logs: `docker logs open-webui`
3. Test API endpoints directly using curl or Postman
4. Verify environment variables are set correctly
5. Review this guide and the main README.md

