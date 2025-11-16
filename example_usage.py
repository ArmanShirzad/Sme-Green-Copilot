"""
Example usage of Green SME Compliance Co-Pilot API

This script demonstrates how to use the API for common compliance tasks.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def example_csrd_energy_audit():
    """Example: CSRD energy audit workflow"""
    print("=" * 60)
    print("Example 1: CSRD Energy Audit")
    print("=" * 60)
    
    chat_input = "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month in Flensburg."
    
    response = requests.post(
        f"{BASE_URL}/workflow/execute",
        json={
            "text": chat_input,
            "userId": 1
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nIntent detected: {result['intent']['intentType']}")
        print(f"Workflow: {result['workflow']['recipeId']}")
        print(f"Forms generated: {result['workflow']['neededForms']}")
        print(f"PDF document: {result['pdfDocument']['docId']}")
        print(f"Compliance pack: {result['compliancePack']}")
        print(f"\nStatus: {result['status']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def example_gdpr_article30():
    """Example: GDPR Article 30 export"""
    print("\n" + "=" * 60)
    print("Example 2: GDPR Article 30 Export")
    print("=" * 60)
    
    chat_input = "I need to generate a GDPR Article 30 processing record for our data processing activities."
    
    response = requests.post(
        f"{BASE_URL}/workflow/execute",
        json={
            "text": chat_input,
            "userId": 1
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nIntent detected: {result['intent']['intentType']}")
        print(f"Regulations: {result['workflow']['regulations']}")
        print(f"Status: {result['status']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def example_emissions_estimation():
    """Example: Standalone emissions estimation"""
    print("\n" + "=" * 60)
    print("Example 3: Emissions Estimation")
    print("=" * 60)
    
    scenarios = [
        {"kWh": 3000, "country": "DE", "description": "German grid"},
        {"kWh": 5000, "country": "FR", "description": "French grid (nuclear)"},
        {"kWh": 2000, "country": "ES", "description": "Spanish grid"}
    ]
    
    for scenario in scenarios:
        response = requests.post(
            f"{BASE_URL}/tools/estimateEmissions",
            json=scenario
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n{scenario['description']}:")
            print(f"  Energy: {result['kWh']} kWh")
            print(f"  Emissions: {result['tCO2e']} tCO2e")
            print(f"  Grid factor: {result['gridFactor']} kg CO2/kWh")
            print(f"  Note: {result['note']}")

def example_intent_detection():
    """Example: Intent detection variations"""
    print("\n" + "=" * 60)
    print("Example 4: Intent Detection Variations")
    print("=" * 60)
    
    test_inputs = [
        "We need CSRD compliance for our energy usage",
        "Generate GDPR Article 30 record",
        "Check if our AI system needs EU AI Act compliance"
    ]
    
    for text in test_inputs:
        response = requests.post(
            f"{BASE_URL}/tools/detectIntent",
            json={"text": text}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nInput: {text}")
            print(f"Intent: {result['intentType']}")
            print(f"Confidence: {result['confidence']}")
            if result['slots']:
                print(f"Slots: {result['slots']}")

if __name__ == '__main__':
    print("\nGreen SME Compliance Co-Pilot - Usage Examples")
    print("=" * 60)
    print("\nMake sure the API server is running:")
    print("  uvicorn main:app --reload")
    print("\nPress Enter to continue...")
    input()
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("ERROR: API server not responding correctly")
            exit(1)
        
        example_intent_detection()
        example_emissions_estimation()
        example_csrd_energy_audit()
        example_gdpr_article30()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to API server.")
        print("Please start the server with: uvicorn main:app --reload")
    except Exception as e:
        print(f"\nERROR: {e}")
