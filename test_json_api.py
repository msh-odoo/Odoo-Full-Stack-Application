#!/usr/bin/env python3
"""Test JSON-RPC API endpoints for service_event_website module"""
import json
import requests

BASE_URL = "http://localhost:8070"
HEADERS = {"Content-Type": "application/json"}

def json_rpc_call(endpoint, params):
    """Make a JSON-RPC 2.0 call"""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": params,
        "id": 1
    }
    response = requests.post(f"{BASE_URL}{endpoint}", json=payload, headers=HEADERS)
    return response.json()

def test_price_api():
    """Test /api/event/price endpoint"""
    print("\n=== Testing /api/event/price ===")
    result = json_rpc_call("/api/event/price", {"event_id": 1, "quantity": 2})
    print(f"Response: {json.dumps(result, indent=2)}")
    return result

def test_availability_api():
    """Test /api/event/availability endpoint"""
    print("\n=== Testing /api/event/availability ===")
    result = json_rpc_call("/api/event/availability", {"event_id": 1, "quantity": 2})
    print(f"Response: {json.dumps(result, indent=2)}")
    return result

def test_validate_api():
    """Test /api/event/validate endpoint"""
    print("\n=== Testing /api/event/validate ===")
    partner_data = {
        "name": "Test Customer",
        "email": "test@example.com",
        "phone": "+1234567890"
    }
    result = json_rpc_call("/api/event/validate", {"event_id": 1, "partner_data": partner_data})
    print(f"Response: {json.dumps(result, indent=2)}")
    return result

if __name__ == "__main__":
    print("Testing Service Event Website JSON-RPC APIs")
    print("=" * 50)
    
    try:
        test_price_api()
        test_availability_api()
        test_validate_api()
        print("\n" + "=" * 50)
        print("✅ All API tests completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
