from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import re
import os
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
import google.generativeai as genai
import google.generativeai as genai

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="BillGuard AI API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnomalyDetector:
    def detect(self, data):
        anomalies = []
        severity = "low"
        
        usage = data.get('usage_kwh', 0)
        
        # 1. Usage Spike
        if usage > 800:
            anomalies.append({
                "type": "Usage Spike",
                "severity": "high",
                "detail": f"Consumption of {usage} kWh exceeds baseline (500 kWh)",
                "impact": f"Estimated ${(usage - 500) * 0.15:.2f} above normal"
            })
            severity = "high"

        # 2. Rate Validation
        t1_rate = data.get('tier1_rate', 0)
        if t1_rate > 0:
            if abs(t1_rate - 0.13) > 0.01:
                t1_usage = data.get('tier1_usage', 0)
                anomalies.append({
                    "type": "Rate Error",
                    "severity": "critical",
                    "detail": f"Tier 1 rate ${t1_rate:.2f}/kWh (expected $0.13/kWh)",
                    "impact": f"Overcharge of ${(t1_rate - 0.13) * t1_usage:.2f}"
                })
                severity = "critical"

        # 3. Calculation Verification
        components = data.get('components_sum', 0)
        total = data.get('total_amount', 0)
        if components > 0 and total > 0:
            diff = abs(total - components)
            if diff > 1.0:
                anomalies.append({
                    "type": "Calculation Error",
                    "severity": "critical",
                    "detail": f"Line items total ${components:.2f}, billed ${total:.2f}",
                    "impact": f"Discrepancy of ${diff:.2f}"
                })
                severity = "critical"

        return anomalies, severity

def extract_data_from_pdf(pdf_bytes):
    try:
        from io import BytesIO
        pdf_file = BytesIO(pdf_bytes)
        
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        data = {}
        patterns = {
            "account_number": r"Account Number:\s*(\d{4}-\d{4}-\d{4})",
            "bill_date": r"Bill Date:\s*([A-Za-z]{3} \d{2}, \d{4})",
            "total_amount": r"Total Due:\s*\$(\d+\.\d{2})",
            # Match the meter reading line: MC-XXXX reading1 reading2 multiplier USAGE
            "usage_kwh": r"MC-\d+\s+[\d,]+\s+[\d,]+\s+[\d.]+\s+(?:<b>)?(\d+)(?:</b>)?",
            "customer_charge": r"Customer Charge.*?\$(\d+\.\d{2})",
            # Tier 1 format: "Tier 1 (First 500 kWh) $0.13 500 kWh $65.00"
            "tier1_rate": r"Tier 1.*?\$(\d+\.\d{2})\s+\d+\s+kWh",
            "tier1_usage": r"Tier 1.*?\$\d+\.\d{2}\s+(\d+)\s+kWh",
            "tier1_cost": r"Tier 1.*?\$\d+\.\d{2}\s+\d+\s+kWh\s+\$(\d+\.\d{2})",
            # Tier 2 format similar
            "tier2_rate": r"Tier 2.*?\$(\d+\.\d{2})\s+\d+\s+kWh",
            "tier2_usage": r"Tier 2.*?\$\d+\.\d{2}\s+(\d+)\s+kWh",
            "tier2_cost": r"Tier 2.*?\$\d+\.\d{2}\s+\d+\s+kWh\s+\$(\d+\.\d{2})",
            "dist_charge": r"Distribution.*?\$(\d+\.\d{2})",
            "taxes": r"Taxes.*?\$(\d+\.\d{2})",
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                val = next((g for g in match.groups() if g is not None), None)
                if val:
                    val = val.replace(',', '')
                    try:
                        if "usage" in key:
                            data[key] = int(val)
                        else:
                            data[key] = float(val)
                    except:
                        pass
        
        # Ensure usage_kwh is set
        if 'usage_kwh' not in data or data['usage_kwh'] == 0:
            # Fallback: try to sum tier usages
            t1 = data.get('tier1_usage', 0)
            t2 = data.get('tier2_usage', 0)
            if t1 > 0:
                data['usage_kwh'] = t1 + t2
        
        comp_sum = 0
        for k in ['customer_charge', 'tier1_cost', 'tier2_cost', 'dist_charge', 'taxes']:
            comp_sum += data.get(k, 0)
        data['components_sum'] = round(comp_sum, 2)
        
        return data
    except Exception as e:
        print(f"Error extracting PDF data: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_ai_summary(data, anomalies):
    if not anomalies:
        return "No irregularities detected. Bill aligns with expected rates and usage patterns."
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    anomaly_text = "\n".join([f"- {a['type']}: {a['detail']}" for a in anomalies])
    
    if api_key and "your_api_key" not in api_key:
        try:
            client = Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[{"role": "user", "content": f"Summarize these billing issues in 2 sentences:\n{anomaly_text}"}]
            )
            return message.content[0].text
        except:
            pass
    
    if "Rate Error" in anomaly_text:
        return "Tier 1 rate incorrectly applied. Contact billing department for rate correction and refund."
    elif "Calculation Error" in anomaly_text:
        return "Mathematical discrepancy detected in total. Request corrected invoice before payment."
    elif "Usage Spike" in anomaly_text:
        return "Significant increase in consumption. Verify meter reading and check for equipment issues."
    return "Multiple issues detected. Manual review recommended."

@app.get("/")
async def root():
    return {"message": "BillGuard AI API", "status": "running"}

@app.post("/api/analyze")
async def analyze_bill(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        # Extract data
        data = extract_data_from_pdf(contents)
        if not data:
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to extract data from PDF"}
            )
        
        # Detect anomalies
        detector = AnomalyDetector()
        anomalies, severity = detector.detect(data)
        
        # Get AI summary
        ai_summary = get_ai_summary(data, anomalies)
        
        return {
            "filename": file.filename,
            "data": data,
            "anomalies": anomalies,
            "severity": severity,
            "ai_summary": ai_summary
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/generate-report")
async def generate_report(data: dict):
    try:
        bill_data = data.get("bill_data", {})
        anomalies = data.get("anomalies", [])
        filename = data.get("filename", "Unknown")
        
        # Build context for Gemini
        context = f"""
You are a senior utility billing analyst. Generate a professional, industry-grade audit report for the following utility bill.

**Bill Information:**
- File: {filename}
- Account: {bill_data.get('account_number', 'N/A')}
- Bill Date: {bill_data.get('bill_date', 'N/A')}
- Total Amount: ${bill_data.get('total_amount', 0):.2f}
- Usage: {bill_data.get('usage_kwh', 0)} kWh
- Effective Rate: ${(bill_data.get('total_amount', 0) / max(1, bill_data.get('usage_kwh', 1))):.3f}/kWh

**Detected Issues:**
"""
        
        if anomalies:
            for i, anomaly in enumerate(anomalies, 1):
                context += f"\n{i}. **{anomaly['type']}** (Severity: {anomaly['severity'].upper()})\n"
                context += f"   - Detail: {anomaly['detail']}\n"
                context += f"   - Financial Impact: {anomaly['impact']}\n"
        else:
            context += "\nNo anomalies detected. Bill appears accurate.\n"
        
        context += """

**Generate a comprehensive report with the following sections:**

1. **Executive Summary** (2-3 sentences)
2. **Bill Overview** (key metrics and comparison to baseline)
3. **Findings & Analysis** (detailed breakdown of each issue)
4. **Financial Impact** (total overcharge/discrepancy amount)
5. **Recommended Actions** (specific, actionable next steps)
6. **Timeline** (suggested deadlines for each action)

Format the report professionally with clear headings and bullet points. Be specific and actionable.
"""
        
        # Call Gemini API
        if not GEMINI_API_KEY:
            return JSONResponse(
                status_code=400,
                content={"error": "Gemini API key not configured"}
            )
        
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response = model.generate_content(context)
        
        return {
            "report": response.text,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/generate-combined-report")
async def generate_combined_report(data: dict):
    try:
        results = data.get("results", [])
        
        if not results:
            return JSONResponse(
                status_code=400,
                content={"error": "No bills provided"}
            )
        
        # Build comprehensive context for Gemini
        context = f"""
You are a senior utility billing analyst. Generate a comprehensive, executive-level audit report for a company analyzing {len(results)} utility bills.

**Company Overview:**
- Total Bills Analyzed: {len(results)}
- Total Issues Found: {sum(len(r.get('anomalies', [])) for r in results)}

**Individual Bill Summaries:**
"""
        
        total_amount = 0
        total_usage = 0
        all_anomalies = []
        
        for i, result in enumerate(results, 1):
            bill_data = result.get('data', {})
            anomalies = result.get('anomalies', [])
            filename = result.get('filename', f'Bill {i}')
            
            total_amount += bill_data.get('total_amount', 0)
            total_usage += bill_data.get('usage_kwh', 0)
            all_anomalies.extend(anomalies)
            
            context += f"\n### Bill {i}: {filename}\n"
            context += f"- Account: {bill_data.get('account_number', 'N/A')}\n"
            context += f"- Date: {bill_data.get('bill_date', 'N/A')}\n"
            context += f"- Amount: ${bill_data.get('total_amount', 0):.2f}\n"
            context += f"- Usage: {bill_data.get('usage_kwh', 0)} kWh\n"
            
            if anomalies:
                context += f"- **Issues ({len(anomalies)}):**\n"
                for anomaly in anomalies:
                    context += f"  - {anomaly['type']}: {anomaly['detail']} ({anomaly['impact']})\n"
            else:
                context += "- Status: ✓ Verified\n"
        
        context += f"""

**Aggregate Metrics:**
- Total Amount Across All Bills: ${total_amount:.2f}
- Total Usage: {total_usage} kWh
- Average Rate: ${(total_amount / max(1, total_usage)):.3f}/kWh
- Critical Issues: {sum(1 for a in all_anomalies if a.get('severity') == 'critical')}
- High Priority Issues: {sum(1 for a in all_anomalies if a.get('severity') == 'high')}

**Generate a comprehensive executive report with the following sections:**

1. **Executive Summary** (3-4 sentences highlighting key findings)
2. **Portfolio Overview** (aggregate metrics and trends)
3. **Critical Findings** (detailed analysis of all issues found)
4. **Financial Impact Analysis** (total overcharges, discrepancies, potential savings)
5. **Bill-by-Bill Breakdown** (summary of each bill's status)
6. **Recommended Actions** (prioritized action items with owners and deadlines)
7. **Risk Assessment** (potential ongoing issues and monitoring recommendations)

Format the report professionally with clear headings, bullet points, and actionable insights suitable for executive review.
"""
        
        # Call Gemini API
        if not GEMINI_API_KEY:
            return JSONResponse(
                status_code=400,
                content={"error": "Gemini API key not configured"}
            )
        
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response = model.generate_content(context)
        
        # Generate PDF
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1e40af',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("BillGuard AI - Combined Audit Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report content
        report_text = response.text
        paragraphs = report_text.split('\n')
        
        for para in paragraphs:
            if para.strip():
                if para.startswith('**') and para.endswith('**'):
                    # Heading
                    story.append(Paragraph(para.replace('**', ''), styles['Heading2']))
                elif para.startswith('#'):
                    # Heading
                    story.append(Paragraph(para.replace('#', '').strip(), styles['Heading3']))
                else:
                    # Normal text
                    story.append(Paragraph(para, styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Return PDF as base64
        import base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return {
            "report": response.text,
            "pdf": pdf_base64,
            "generated_at": datetime.now().isoformat(),
            "bills_analyzed": len(results),
            "total_issues": len(all_anomalies)
        }
    
    except Exception as e:
        print(f"Error generating combined report: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
