import requests
import json

BASE_URL = "http://localhost:8000"

def test_detect_intent():
    """Test intent detection endpoint"""
    response = requests.post(
        f"{BASE_URL}/tools/detectIntent",
        json={"text": "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month in Flensburg."}
    )
    print("Detect Intent:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_select_workflow(intent_result):
    """Test workflow selection"""
    response = requests.post(
        f"{BASE_URL}/tools/selectWorkflow",
        json=intent_result
    )
    print("\nSelect Workflow:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_estimate_emissions():
    """Test emissions estimation"""
    response = requests.post(
        f"{BASE_URL}/tools/estimateEmissions",
        json={"kWh": 3000, "country": "DE"}
    )
    print("\nEstimate Emissions:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_execute_workflow():
    """Test complete workflow execution"""
    response = requests.post(
        f"{BASE_URL}/workflow/execute",
        json={
            "text": "I need an energy audit for CSRD compliance. We consumed 3000 kWh last month.",
            "userId": 1
        }
    )
    print("\nExecute Workflow:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

if __name__ == '__main__':
    print("Testing Green SME Compliance Co-Pilot API\n")
    print("=" * 50)
    
    try:
        intent = test_detect_intent()
        workflow = test_select_workflow(intent)
        emissions = test_estimate_emissions()
        result = test_execute_workflow()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print("ERROR: API server not running. Start with: uvicorn main:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
