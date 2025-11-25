# ⚡ Utility Bill Anomaly Detector POC

A visually stunning, AI-powered proof-of-concept application for detecting anomalies in utility bills. This tool demonstrates a modern approach to document processing, combining OCR, rule-based logic, and Generative AI to provide actionable insights.

## 🌟 Key Features

-   **Visual Workflow**: Interactive "How It Works" section demonstrating the data pipeline.
-   **Realistic Bill Generation**: Creates industry-standard PDF utility bills for testing.
-   **Multi-Layered Detection**: Identifies usage spikes, calculation errors, and rate mismatches.
-   **AI-Powered Insights**: Uses Claude (Anthropic) to generate human-readable summaries of anomalies.
-   **Production-Ready Design**: Professional UI with custom CSS, interactive charts, and a scaling strategy.

## 🛠️ Tech Stack

-   **Frontend**: Streamlit (with custom CSS & components)
-   **PDF Processing**: `pdfplumber` (Extraction), `weasyprint` (Generation)
-   **AI Engine**: Anthropic Claude API
-   **Visualization**: Plotly, Streamlit Extras

## 🚀 Quick Start

### Prerequisites

-   Python 3.9+
-   **WeasyPrint Dependencies**:
    -   **Windows**: You may need to install GTK3. Follow the [WeasyPrint Windows installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).
    -   **Mac/Linux**: Install via Homebrew (`brew install weasyprint`) or your package manager.

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd UCM_POC
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**
    -   Copy `.env.example` to `.env`
    -   Add your Anthropic API Key:
        ```
        ANTHROPIC_API_KEY=sk-ant-...
        ```

### Running the Demo

1.  **Generate Sample Bills**
    Run the generation script to create 4 realistic PDF bills in the `generated_bills/` directory.
    ```bash
    python generate_bills.py
    ```

2.  **Launch the App**
    ```bash
    streamlit run app.py
    ```

## 🎨 Design Philosophy

This POC is designed to emulate a high-end **Enterprise SaaS** platform (e.g., Stripe, Vercel).
-   **Data-First Aesthetic**: Clean "Slate" color palette, high-contrast typography (Inter), and subtle shadows.
-   **Trust & Clarity**: No gimmicks. Professional "Audit Dashboard" layout with clear pipeline visualization.
-   **Actionable Intelligence**: Anomalies are presented as "Auditor Notes" with clear financial impact.

## 📈 Scaling Strategy

Check the "Scaling to Production" section in the app for a detailed breakdown of:
-   **Architecture**: Microservices approach.
-   **Data Pipeline**: Async processing with queues.
-   **ML Enhancements**: Moving from rules to predictive models.
