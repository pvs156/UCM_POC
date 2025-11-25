import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Ensure output directory exists
OUTPUT_DIR = "generated_bills"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- BILL DATA SCENARIOS ---
bills = [
    {
        "filename": "bill1_normal.pdf",
        "account_number": "8271-4523-0019",
        "address": "123 Maple Ave, Metro City",
        "bill_date": "Oct 01, 2024",
        "period": "Sep 01, 2024 - Sep 30, 2024",
        "due_date": "Oct 20, 2024",
        "meter_number": "MC-8842",
        "prev_reading": "45,320",
        "curr_reading": "45,900",
        "usage_kwh": 580,
        "charges": [
            ["Customer Charge", "Fixed", "-", "$10.00"],
            ["Energy Charge - Tier 1 (First 500 kWh)", "$0.13", "500 kWh", "$65.00"],
            ["Energy Charge - Tier 2 (Over 500 kWh)", "$0.17", "80 kWh", "$13.60"],
            ["Distribution Charges", "Variable", "-", "$8.00"],
            ["Taxes & Fees", "~10%", "-", "$9.66"],
            ["Total Electric Charges", "", "", "$106.26"]
        ],
        "total_amount": "106.26",
        "history": [40, 45, 42, 38, 35, 30, 28, 32, 45, 50, 48, 58]
    },
    {
        "filename": "bill2_spike.pdf",
        "account_number": "8271-4523-0019",
        "address": "123 Maple Ave, Metro City",
        "bill_date": "Nov 01, 2024",
        "period": "Oct 01, 2024 - Oct 31, 2024",
        "due_date": "Nov 20, 2024",
        "meter_number": "MC-8842",
        "prev_reading": "45,900",
        "curr_reading": "46,845",
        "usage_kwh": 945,
        "charges": [
            ["Customer Charge", "Fixed", "-", "$10.00"],
            ["Energy Charge - Tier 1 (First 500 kWh)", "$0.13", "500 kWh", "$65.00"],
            ["Energy Charge - Tier 2 (Over 500 kWh)", "$0.17", "445 kWh", "$75.65"],
            ["Distribution Charges", "Variable", "-", "$12.00"],
            ["Taxes & Fees", "~10%", "-", "$16.27"],
            ["Total Electric Charges", "", "", "$178.92"]
        ],
        "total_amount": "178.92",
        "history": [45, 42, 38, 35, 30, 28, 32, 45, 50, 48, 58, 95]
    },
    {
        "filename": "bill3_math_error.pdf",
        "account_number": "9384-6172-0041",
        "address": "789 Oak Ln, Metro City",
        "bill_date": "Nov 01, 2024",
        "period": "Oct 01, 2024 - Oct 31, 2024",
        "due_date": "Nov 20, 2024",
        "meter_number": "MC-1129",
        "prev_reading": "12,100",
        "curr_reading": "12,720",
        "usage_kwh": 620,
        "charges": [
            ["Customer Charge", "Fixed", "-", "$10.00"],
            ["Energy Charge - Tier 1 (First 500 kWh)", "$0.13", "500 kWh", "$65.00"],
            ["Energy Charge - Tier 2 (Over 500 kWh)", "$0.17", "120 kWh", "$20.40"],
            ["Distribution Charges", "Variable", "-", "$9.00"],
            ["Taxes & Fees", "~10%", "-", "$10.44"],
            ["Total Electric Charges", "", "", "$121.84"] # ERROR: Should be 114.84
        ],
        "total_amount": "121.84",
        "history": [60, 62, 58, 55, 50, 48, 52, 58, 65, 60, 62, 62]
    },
    {
        "filename": "bill4_wrong_rate.pdf",
        "account_number": "7159-2846-0033",
        "address": "456 Pine St, Metro City",
        "bill_date": "Nov 01, 2024",
        "period": "Oct 01, 2024 - Oct 31, 2024",
        "due_date": "Nov 20, 2024",
        "meter_number": "MC-5531",
        "prev_reading": "88,200",
        "curr_reading": "88,950",
        "usage_kwh": 750,
        "charges": [
            ["Customer Charge", "Fixed", "-", "$10.00"],
            ["Energy Charge - Tier 1 (First 500 kWh)", "$0.15", "500 kWh", "$75.00"], # WRONG RATE
            ["Energy Charge - Tier 2 (Over 500 kWh)", "$0.17", "250 kWh", "$42.50"],
            ["Distribution Charges", "Variable", "-", "$10.50"],
            ["Taxes & Fees", "~10%", "-", "$13.80"],
            ["Total Electric Charges", "", "", "$151.80"]
        ],
        "total_amount": "151.80",
        "history": [70, 72, 68, 65, 60, 58, 62, 68, 75, 70, 72, 75]
    }
]

def create_bill(bill_data):
    filepath = os.path.join(OUTPUT_DIR, bill_data['filename'])
    doc = SimpleDocTemplate(filepath, pagesize=LETTER, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#0056b3'), spaceAfter=20)
    header_info_style = ParagraphStyle('HeaderInfo', parent=styles['Normal'], fontSize=10, textColor=colors.gray, alignment=2) # Right align
    section_header = ParagraphStyle('SectionHeader', parent=styles['Heading3'], fontSize=14, textColor=colors.HexColor('#0056b3'), spaceBefore=20, spaceAfter=10, borderPadding=5, borderColor=colors.HexColor('#ddd'), borderWidth=0, borderBottomWidth=1)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10)
    
    # --- HEADER ---
    # Logo/Title and Company Info in a table
    header_data = [
        [Paragraph("<b>METRO CITY POWER</b>", title_style), 
         Paragraph("123 Utility Way, Metro City, ST 12345<br/>Customer Service: 1-800-555-0199<br/>www.metrocitypower.com", header_info_style)]
    ]
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor('#0056b3')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # --- SUMMARY BOX ---
    # Account Info | Bill Summary
    summary_data = [
        [
            Paragraph(f"<b>Account Number:</b> {bill_data['account_number']}<br/><b>Service Address:</b> {bill_data['address']}<br/><b>Bill Date:</b> {bill_data['bill_date']}<br/><b>Billing Period:</b> {bill_data['period']}", normal_style),
            Paragraph(f"Previous Balance: $0.00<br/>Payments Received: $0.00<br/>Total New Charges: ${bill_data['total_amount']}<br/><font size=14 color='#0056b3'><b>Total Due: ${bill_data['total_amount']}</b></font><br/><font color='red'>Due Date: {bill_data['due_date']}</font>", ParagraphStyle('RightAlign', parent=normal_style, alignment=2))
        ]
    ]
    summary_table = Table(summary_data, colWidths=[3.5*inch, 3.5*inch])
    summary_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#ddd')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    
    # --- USAGE HISTORY GRAPH ---
    story.append(Paragraph("12-Month Usage History (kWh)", section_header))
    
    # Create a simple bar chart
    d = Drawing(400, 150)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 20
    bc.height = 125
    bc.width = 350
    bc.data = [bill_data['history']]
    bc.strokeColor = colors.white
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(bill_data['history']) + 20
    bc.valueAxis.valueStep = 20
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.categoryAxis.labels.dx = 8
    bc.categoryAxis.labels.dy = -2
    bc.categoryAxis.labels.angle = 0
    bc.bars[0].fillColor = colors.HexColor('#cbd5e0')
    # Highlight last bar
    # ReportLab charts are a bit tricky to style individually without complex logic, 
    # so we'll just keep them uniform for this POC or try to hack it if needed.
    # For now, uniform is fine, maybe change color of the whole series.
    
    d.add(bc)
    story.append(d)
    story.append(Spacer(1, 10))
    
    # --- METER READING ---
    story.append(Paragraph("Meter Reading Details", section_header))
    meter_data = [
        ["Meter Number", "Previous Reading", "Current Reading", "Multiplier", "Total Usage (kWh)"],
        [bill_data['meter_number'], bill_data['prev_reading'], bill_data['curr_reading'], "1.0", f"<b>{bill_data['usage_kwh']}</b>"]
    ]
    meter_table = Table(meter_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch, 1.5*inch])
    meter_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#555555')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#eee')),
    ]))
    story.append(meter_table)
    
    # --- CHARGES BREAKDOWN ---
    story.append(Paragraph("Electric Charges Detail", section_header))
    
    charges_header = ["Description", "Rate/Unit", "Usage", "Amount"]
    charges_data = [charges_header] + bill_data['charges']
    
    charges_table = Table(charges_data, colWidths=[3.5*inch, 1*inch, 1.5*inch, 1*inch])
    charges_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#555555')),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('LINEBELOW', (0,0), (-1,-2), 1, colors.HexColor('#eee')),
        ('LINEABOVE', (0,-1), (-1,-1), 2, colors.black), # Total row line
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ]))
    story.append(charges_table)
    
    story.append(Spacer(1, 20))
    
    # --- MESSAGE BOX ---
    msg_text = "<b>Important Message:</b> Save energy and money by switching to LED bulbs! Visit our website for rebates."
    msg = Paragraph(msg_text, ParagraphStyle('Msg', parent=normal_style, backColor=colors.HexColor('#e6f2ff'), borderColor=colors.HexColor('#cce5ff'), borderWidth=1, borderPadding=10))
    story.append(msg)
    
    story.append(Spacer(1, 40))
    
    # --- FOOTER ---
    footer_text = f"Please return this portion with your payment. Make checks payable to Metro City Power.<br/>Account: {bill_data['account_number']} | Amount Due: ${bill_data['total_amount']} | Due by: {bill_data['due_date']}"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, alignment=1, textColor=colors.gray, fontSize=9))
    story.append(footer)
    
    doc.build(story)
    print(f"Created {filepath}")

def generate_bills():
    print("Generating bills with ReportLab...")
    for bill in bills:
        create_bill(bill)
    print("Done!")

if __name__ == "__main__":
    generate_bills()
