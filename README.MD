# Canadian Credit Optimization Streamlit App

A lightweight Streamlit app for modeling month-by-month credit utilization reduction and repayment strategy for the Canadian credit ecosystem.

## Files

- `app.py` — Streamlit application.
- `requirements.txt` — Python dependency list for Streamlit deployment.

## Supported Model

- Supports a dynamic number of credit cards and one or more unsecured lines of credit.
- The app aggregates balances and limits across all revolving accounts to compute Canadian credit utilization.
- It estimates the number of months required to improve score based on your monthly paydown budget and utilization reduction.
- It now allows you to set a desired target horizon and compares the projected timeline against that goal.

## Local Setup

1. Create a Python environment:
   - `python -m venv .venv`
   - `.\venv\Scripts\activate` (PowerShell)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run locally:
   - `streamlit run app.py`

## Free Hosting on Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to https://share.streamlit.io.
3. Connect your GitHub account and deploy the repo.
4. Select `app.py` as the main file.

## Notes

- This app uses Canadian-credit-specific terminology and CAD values.
- The timeline is a deterministic simulation and should be validated with actual bureau data before productizing.
