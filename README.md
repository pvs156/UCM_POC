# Utility Bill Anomaly Detector (proof of concept)

A Streamlit demo that checks utility bill PDFs for usage spikes, rate mismatches, and arithmetic errors. It can use Claude to summarize detected issues in plain language.

## Architecture

```text
PDF upload → pdfplumber text extraction → field parsing → rule-based anomaly checks
                                                     └→ optional Claude summary → Streamlit results
```

`app.py` handles uploads, extraction, rules, and the UI. `generate_bills.py` uses ReportLab to create sample PDF bills. If `ANTHROPIC_API_KEY` is absent or the API call fails, the app uses a rule-based summary. The detector works without an API key.

This app extracts text from PDFs; it does **not** perform OCR on scanned images.

## Stack

Python, Streamlit, pdfplumber, ReportLab, Plotly, and the Anthropic Python SDK.

## Run locally

Requires Python 3.9 or later.

```bash
git clone https://github.com/pvs156/UCM_POC.git
cd UCM_POC
python -m venv .venv
# Activate .venv for your shell.
pip install -r requirements.txt
cp .env.example .env
python generate_bills.py
streamlit run app.py
```

Set `ANTHROPIC_API_KEY` in `.env` to enable Claude summaries. You can also set `ANTHROPIC_MODEL`; the default is `claude-sonnet-4-6`. Do not commit `.env`. Open the local URL printed by Streamlit and upload one of the generated bills or a text-based bill PDF.

## Results and evaluation

The repository includes generated sample bills for a manual walkthrough. It does not publish a labeled test set, precision/recall, or a measured accuracy claim. The code reports anomalies from fixed rules; Claude explains those results and does not determine whether the bill is correct.

## Limits

- Parsing expects the bill formats used in this proof of concept; other layouts may need new extraction rules.
- Scanned PDFs need an OCR step before this app can analyze them.
- Rules and AI summaries are aids for review, not a substitute for checking the original bill.
