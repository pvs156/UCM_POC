import requests, json, base64

url = 'http://127.0.0.1:8000/api/generate-combined-report'
payload = {
    "results": [
        {
            "filename": "Bill1.pdf",
            "data": {"usage_kwh": 1000, "total_amount": 200},
            "anomalies": [
                {"type": "Overcharge", "impact": "$50", "detail": "Overcharge detected", "severity": "medium"}
            ],
            "ai_summary": "Summary of Bill1"
        },
        {
            "filename": "Bill2.pdf",
            "data": {"usage_kwh": 1500, "total_amount": 300},
            "anomalies": [],
            "ai_summary": "Summary of Bill2"
        }
    ]
}

headers = {'Content-Type': 'application/json'}
resp = requests.post(url, data=json.dumps(payload), headers=headers)
print('Status:', resp.status_code)
print('Response:', resp.json())
if resp.status_code == 200:
    data = resp.json()
    if 'pdf' in data:
        pdf_bytes = base64.b64decode(data['pdf'])
        with open('combined_report_test.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print('PDF saved as combined_report_test.pdf')
