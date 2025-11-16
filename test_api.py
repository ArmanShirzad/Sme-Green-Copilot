#!/usr/bin/env python3
"""
Simple test script for Green SME Compliance Co-Pilot API
Run this after starting the FastAPI server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_detect_intent():
    """Test intent detection"""
    print("Testing intent detection...")
    test_cases = [
        "I need an energy audit for CSRD compliance",
        "Generate GDPR Article 30 record",
        "Check AI system risks for EU AI Act"
    ]
    
    for text in test_cases:
        response = requests.post(
            f"{BASE_URL}/tools/detectIntent",
            json={"text": text}
        )
        print(f"Input: {text}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()

def test_estimate_emissions():
    """Test emissions estimation"""
    print("Testing emissions estimation...")
    response = requests.post(
        f"{BASE_URL}/tools/estimateEmissions",
        json={"kWh": 3000, "country": "DE"}
    )
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_select_workflow():
    """Test workflow selection"""
    print("Testing workflow selection...")
    response = requests.post(
        f"{BASE_URL}/tools/selectWorkflow",
        json={
            "intentType": "energyAuditForCSRD",
            "slots": {"kWh": 3000, "city": "Flensburg"}
        }
    )
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_classify_ai_risk():
    """Test AI risk classification"""
    print("Testing AI risk classification...")
    response = requests.post(
        f"{BASE_URL}/tools/classifyAIRisk",
        json={"description": "Biometric identification system for employee access"}
    )
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Green SME Compliance Co-Pilot API Tests")
    print("=" * 60)
    print()
    
    try:
        test_health()
        test_detect_intent()
        test_estimate_emissions()
        test_select_workflow()
        test_classify_ai_risk()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"Error: {e}")
