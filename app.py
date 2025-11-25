import streamlit as st
import pdfplumber
import re
import os
import time
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Force reload - v2

st.set_page_config(
    page_title="Bill Auditor",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal, professional CSS
st.markdown("""
<style>
    @import url('https://rsms.me/inter/inter.css');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: #fafafa;
    }
    
    /* Remove Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Clean header */
    .main-header {
        padding: 2rem 0 1rem 0;
        border-bottom: 1px solid #e5e5e5;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #171717;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        font-size: 0.875rem;
        color: #737373;
        margin-top: 0.25rem;
    }
    
    /* Bill cards */
    .bill-card {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .bill-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.25rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #f5f5f5;
    }
    
    .bill-filename {
        font-size: 0.875rem;
        font-weight: 500;
        color: #171717;
    }
    
    .bill-meta {
        font-size: 0.75rem;
        color: #a3a3a3;
        margin-top: 0.25rem;
    }
    
    .status-badge {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.625rem;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    .status-pass {
        background: #f0fdf4;
        color: #166534;
    }
    
    .status-fail {
        background: #fef2f2;
        color: #991b1b;
    }
    
    /* Metrics */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .metric {
        display: flex;
        flex-direction: column;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #737373;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #171717;
        font-variant-numeric: tabular-nums;
    }
    
    /* Issues */
    .issue {
        background: #fafafa;
        border-left: 2px solid #d4d4d4;
        padding: 0.875rem;
        margin-bottom: 0.75rem;
        border-radius: 4px;
    }
    
    .issue.critical {
        background: #fef2f2;
        border-left-color: #dc2626;
    }
    
    .issue-title {
        font-size: 0.8125rem;
        font-weight: 600;
        color: #171717;
        margin-bottom: 0.25rem;
    }
    
    .issue-detail {
        font-size: 0.8125rem;
        color: #525252;
        line-height: 1.5;
    }
    
    .issue-impact {
        font-size: 0.75rem;
        color: #737373;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* AI note */
    .ai-note {
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 1rem;
        margin-top: 1.5rem;
    }
    
    .ai-note-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #525252;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .ai-note-text {
        font-size: 0.875rem;
        color: #171717;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# Helper classes
class AnomalyDetector:
    def detect(self, data):
        anomalies = []
        severity = "low"
        
        usage = data.get('usage_kwh', 0)
        
        if usage > 800:
            anomalies.append({
                "type": "Usage Spike",
                "severity": "high",
                "detail": f"Consumption of {usage} kWh exceeds baseline (500 kWh)",
                "impact": f"Estimated ${(usage - 500) * 0.15:.2f} above normal"
            })
            severity = "high"

        t1_usage = data.get('tier1_usage', 0)
        t1_cost = data.get('tier1_cost', 0)
        if t1_usage > 0 and t1_cost > 0:
            rate = t1_cost / t1_usage
            if abs(rate - 0.13) > 0.01:
                anomalies.append({
                    "type": "Rate Error",
                    "severity": "critical",
                    "detail": f"Tier 1 rate ${rate:.2f}/kWh (expected $0.13/kWh)",
                    "impact": f"Overcharge of ${(rate - 0.13) * t1_usage:.2f}"
                })
                severity = "critical"

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

def extract_data_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        data = {}
        patterns = {
            "account_number": r"Account Number:\s*(\d{4}-\d{4}-\d{4})",
            "bill_date": r"Bill Date:\s*([A-Za-z]{3} \d{2}, \d{4})",
            "total_amount": r"Total Due:\s*\$([\d,]+\.\d{2})",
            "usage_kwh_explicit": r"(?:Total Usage \(kWh\)\s*(\d+)|MC-\d+.*?(\d+)\s*$)",
            "customer_charge": r"Customer Charge.*?\$(\d+\.\d{2})",
            "tier1_cost": r"Energy Charge - Tier 1.*?kWh\s*\$(\d+\.\d{2})",
            "tier2_cost": r"Energy Charge - Tier 2.*?kWh\s*\$(\d+\.\d{2})",
            "dist_charge": r"Distribution Charges.*?\$(\d+\.\d{2})",
            "taxes": r"Taxes & Fees.*?\$(\d+\.\d{2})",
            "tier1_usage": r"Energy Charge - Tier 1.*?(\d+)\s*kWh",
            "tier2_usage": r"Energy Charge - Tier 2.*?(\d+)\s*kWh",
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
        
        if 'usage_kwh_explicit' in data:
            data['usage_kwh'] = data['usage_kwh_explicit']
        else:
            t1 = data.get('tier1_usage', 0)
            t2 = data.get('tier2_usage', 0)
            if t1 > 0:
                data['usage_kwh'] = t1 + t2
        
        comp_sum = 0
        for k in ['customer_charge', 'tier1_cost', 'tier2_cost', 'dist_charge', 'taxes']:
            comp_sum += data.get(k, 0)
        data['components_sum'] = round(comp_sum, 2)
        
        return data, text
    except:
        return None, None

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

# Main app
st.markdown("""
<div class="main-header">
    <h1 class="main-title">Bill Auditor</h1>
    <p class="main-subtitle">Automated utility bill verification</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Upload bills (PDF)", type="pdf", accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Analyzing {uploaded_file.name}..."):
            time.sleep(0.5)
            data, _ = extract_data_from_pdf(uploaded_file)
            
            if data:
                detector = AnomalyDetector()
                anomalies, severity = detector.detect(data)
                ai_summary = get_ai_summary(data, anomalies)
                
                status_class = "status-fail" if anomalies else "status-pass"
                status_text = f"{len(anomalies)} Issues" if anomalies else "Verified"
                
                issues_html = ""
                if anomalies:
                    for a in anomalies:
                        issue_class = "critical" if a['severity'] == 'critical' else ""
                        issues_html += f"""
                        <div class="issue {issue_class}">
                            <div class="issue-title">{a['type']}</div>
                            <div class="issue-detail">{a['detail']}</div>
                            <div class="issue-impact">{a['impact']}</div>
                        </div>
                        """
                
                st.markdown(f"""
                <div class="bill-card">
                    <div class="bill-card-header">
                        <div>
                            <div class="bill-filename">{uploaded_file.name}</div>
                            <div class="bill-meta">{data.get('account_number', 'N/A')} · {data.get('bill_date', 'N/A')}</div>
                        </div>
                        <div class="status-badge {status_class}">{status_text}</div>
                    </div>
                    
                    <div class="metrics-row">
                        <div class="metric">
                            <div class="metric-label">Usage</div>
                            <div class="metric-value">{data.get('usage_kwh', 0):,} kWh</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Amount</div>
                            <div class="metric-value">${data.get('total_amount', 0):.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Rate</div>
                            <div class="metric-value">${data.get('total_amount', 0)/max(1, data.get('usage_kwh', 1)):.3f}/kWh</div>
                        </div>
                    </div>
                    
                    {issues_html if issues_html else '<div class="issue"><div class="issue-detail">All checks passed</div></div>'}
                    
                    <div class="ai-note">
                        <div class="ai-note-label">Analysis</div>
                        <div class="ai-note-text">{ai_summary}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
