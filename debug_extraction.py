import pdfplumber
import re
import os

def debug_pdf(filename):
    path = os.path.join("generated_bills", filename)
    print(f"--- Debugging {filename} ---")
    
    try:
        with pdfplumber.open(path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
                
        print("RAW TEXT OUTPUT:")
        print("--------------------------------------------------")
        print(text)
        print("--------------------------------------------------")
        
        # Test robust regex patterns
        patterns = {
            # Look for Meter ID followed by readings and multiplier 1.0 then the usage
            "meter_row_usage": r"MC-\d+\s+[\d,]+\s+[\d,]+\s+1\.0\s+(\d+)",
            "usage_kwh_original": r"(?:Total Usage \(kWh\)\s*(\d+)|MC-\d+.*?(\d+)\s*$)",
        }
        
        print("\nREGEX MATCHES:")
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                print(f"{key}: MATCH -> {match.groups()}")
            else:
                print(f"{key}: NO MATCH")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_pdf("bill1_normal.pdf")
