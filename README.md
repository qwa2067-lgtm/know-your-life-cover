# Know Your Life Cover

[![Live App](https://img.shields.io/badge/Live%20App-know--your--life--cover.streamlit.app-brightgreen?style=for-the-badge)](https://know-your-life-cover.streamlit.app)

A Streamlit dashboard that compares the life cover sections of three Australian life insurance Product Disclosure Statements (PDS) — TAL Accelerated Protection, AIA Priority Protection, and Zurich Active.

Built to help customers understand what they are buying before they sit down with a financial adviser.

---

## What It Does

**6 tabs, designed for a customer audience:**

| Tab | Purpose |
|-----|---------|
| Overview | Side-by-side snapshot of key numbers — sum insured limits, expiry ages, terminal illness thresholds, funeral advances |
| My Situation | Rule-based flag engine — answer 8 questions about your situation and see which policy terms are most relevant to you |
| Side-by-Side Compare | Full feature comparison across all three insurers, with equivalent features aligned horizontally |
| Watch Out For | Policy terms that customers may not notice when reading a PDS — non-disclosure rules, exclusions, benefit interactions |
| Know Your Rights | Summary of customer protections under the Life Insurance Code of Practice |
| Disclaimer | Scope and limitations of the tool |

---

## Why I Built This

Life insurance PDS documents are long, dense, and written in legal language. Customers often sign policies without understanding the exact terms — particularly around terminal illness definitions, what reduces the sum insured, and when exclusions apply.

This tool extracts and restructures that information so customers can arrive at an advisory conversation already informed.

---

## Technical Stack

- **Python / Streamlit** — dashboard framework
- **pdfplumber** — PDF text extraction from raw PDS files
- **Anthropic Claude API** — structured data extraction from PDS text (via `extract_pds.py`)
- **Hand-built HTML tables** — used in place of `st.dataframe` for readable multi-line cells
- **Rule engine** — form-driven flag logic in the My Situation tab

---

## Project Structure

```
PDSCompareTool/
├── app.py              # Main dashboard
├── extract_pds.py      # One-time PDS extraction script (requires API key)
├── pds_data.json       # Structured PDS data (output of extract_pds.py)
├── requirements.txt
└── .gitignore
```

PDFs are excluded from this repository (copyright material). To re-extract data from updated PDFs, place them in the project folder and run `extract_pds.py` with an Anthropic API key.

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Data Sources

All information in this dashboard is sourced directly from publicly available Product Disclosure Statements:

- TAL Accelerated Protection PDS (December 2025)
- AIA Priority Protection PDS (9 November 2025)
- Zurich Active PDS (1 November 2025)
- Life Insurance Code of Practice (March 2025, Version 2)

---

## Disclaimer

This dashboard is for **informational purposes only**. It is not financial advice and does not constitute a recommendation of any product.

Two limitations to be aware of:

1. **PDS versions change.** Insurers periodically release updated documents. Information here may not reflect the current version of a product.
2. **Interpretation may not be perfect.** Policy wording is complex and some nuance may have been lost in summarisation. Do not rely on this tool as a definitive legal or contractual interpretation.

This is a working prototype built to demonstrate the application of insurance domain expertise to a customer transparency problem. It has not been independently audited or reviewed by the named insurers. Always read the current PDS and consult a licensed financial adviser before purchasing life insurance.

---

*Built by Amy Wang — actuary (FIAA), 11 years in Australian life insurance and reinsurance.*
