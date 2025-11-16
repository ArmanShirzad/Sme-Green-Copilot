#!/bin/bash
# Test script for Green SME Compliance Co-Pilot API endpoints

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Green SME Compliance Co-Pilot API Tests"
echo "=========================================="
echo ""

# Check if server is running
echo "1. Testing server health..."
response=$(curl -s "$BASE_URL/")
if [ $? -eq 0 ]; then
    echo "✓ Server is running"
    echo "$response" | jq .
else
    echo "✗ Server is not running. Start it with: ./run.sh"
    exit 1
fi
echo ""

# Test intent detection
echo "2. Testing intent detection..."
response=$(curl -s -X POST "$BASE_URL/tools/detectIntent" \
    -H "Content-Type: application/json" \
    -d '{"text": "I need help with energy audit for CSRD. We used 3200 kWh in Flensburg"}')
echo "$response" | jq .
echo ""

# Test workflow selection
echo "3. Testing workflow selection..."
response=$(curl -s -X POST "$BASE_URL/tools/selectWorkflow" \
    -H "Content-Type: application/json" \
    -d '{
        "intentType": "energyAuditForCSRD",
        "slots": {"kWh": 3200, "city": "Flensburg"},
        "userId": 1
    }')
echo "$response" | jq .
echo ""

# Test emissions calculation
echo "4. Testing emissions calculation..."
response=$(curl -s -X POST "$BASE_URL/tools/estimateEmissions" \
    -H "Content-Type: application/json" \
    -d '{"kWh": 3200, "gridFactor": 0.42}')
echo "$response" | jq .
echo ""

# Test weather insights
echo "5. Testing weather insights..."
response=$(curl -s -X POST "$BASE_URL/tools/getWeatherInsight" \
    -H "Content-Type: application/json" \
    -d '{"city": "Flensburg", "country": "DE"}')
echo "$response" | jq .
echo ""

# Test load shift recommendations
echo "6. Testing load shift recommendations..."
response=$(curl -s -X POST "$BASE_URL/tools/suggestLoadShift" \
    -H "Content-Type: application/json" \
    -d '{
        "kWhProfile": {"morning": 800, "afternoon": 1200, "evening": 1200},
        "weatherHint": {"sunHours": 6.5}
    }')
echo "$response" | jq .
echo ""

# Test PDF generation
echo "7. Testing PDF generation..."
response=$(curl -s -X POST "$BASE_URL/tools/fillPdf" \
    -H "Content-Type: application/json" \
    -d '{
        "formId": "vsme_snapshot",
        "fieldValues": {
            "name": "Prime Bakery GmbH",
            "address": "Flensburger Strasse 1",
            "city": "Flensburg",
            "postal_code": "24937",
            "kWh": 3200,
            "tCO2e": 1.34,
            "methodology": "Calculated using German grid factor 0.42 kg/kWh",
            "actions": "LED lighting upgrade planned for Q1 2025"
        }
    }')
echo "$response" | jq .
doc_id=$(echo "$response" | jq -r '.docId')
echo "Document ID: $doc_id"
echo ""

# Test compliance pack generation
echo "8. Testing compliance pack generation..."
response=$(curl -s -X POST "$BASE_URL/tools/generateCompliancePack" \
    -H "Content-Type: application/json" \
    -d '{
        "submissionId": 1,
        "regulations": ["CSRD", "VSME", "EU_AI_Act"]
    }')
echo "$response" | jq .
echo ""

# Test user profile fetch
echo "9. Testing user profile fetch..."
response=$(curl -s "$BASE_URL/user/1")
echo "$response" | jq .
echo ""

# Test submissions fetch
echo "10. Testing submissions fetch..."
response=$(curl -s "$BASE_URL/submissions/1")
echo "$response" | jq .
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
echo ""
echo "Check generated files in ./outputs/"
ls -lh outputs/ | tail -5
