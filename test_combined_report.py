import requests
import json

# Test data matching the structure from frontend
test_data = {
    "results": [
        {
            "filename": "test_bill_1.pdf",
            "data": {
                "account_number": "123456",
                "bill_date": "2024-01-15",
                "total_amount": 150.50,
                "usage_kwh": 1000
            },
            "anomalies": [
                {
                    "type": "Rate Discrepancy",
                    "detail": "Charged rate exceeds approved tariff",
                    "impact": "Overcharge of $25.00",
                    "severity": "high"
                }
            ]
        },
        {
            "filename": "test_bill_2.pdf",
            "data": {
                "account_number": "789012",
                "bill_date": "2024-01-20",
                "total_amount": 200.75,
                "usage_kwh": 1500
            },
            "anomalies": []
        }
    ]
}

# Make request
try:
    response = requests.post(
        'http://localhost:8000/api/generate-combined-report',
        json=test_data,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")  # First 500 chars
    
    if response.ok:
        data = response.json()
        print("\n✅ SUCCESS!")
        print(f"Bills analyzed: {data.get('bills_analyzed')}")
        print(f"Total issues: {data.get('total_issues')}")
        print(f"Has PDF: {'pdf' in data}")
        print(f"Report length: {len(data.get('report', ''))}")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
