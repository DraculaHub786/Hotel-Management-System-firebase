# Nur-e-Haya — Deployment & Operations Guide

## Overview
This platform runs on Python 3.11 with Flask 3 blueprint architecture and Google Cloud Firebase Firestore.

## Quick Start (Local Development)

1. **Clone and setup virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate # Linux/macOS
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and configure:
   ```env
   FLASK_ENV=development
   SECRET_KEY=your_secret_key_here
   FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
   PORT=5000
   ```

4. **Run Application**:
   ```bash
   python app.py
   ```
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Seed Accounts (Password: `Hotel@123`)

| Email | Role | Department / Description |
|---|---|---|
| `admin@nur-e-haya.com` | `admin` | Full system administrator |
| `manager@nur-e-haya.com` | `manager` | General hotel operations manager |
| `chef@nur-e-haya.com` | `chef` | Head Chef (Kitchen queue) |
| `frontdesk@nur-e-haya.com` | `front_desk` | Front Desk Reception & Night Audit |
| `cleaning@nur-e-haya.com` | `housekeeping` | Housekeeping staff & linen tracker |
| `laundry@nur-e-haya.com` | `laundry` | Laundry operations |
| `maintenance@nur-e-haya.com` | `maintenance` | Chief Engineer & Work orders |
| `concierge@nur-e-haya.com` | `concierge` | Concierge & Transfers |
| `accountant@nur-e-haya.com` | `accountant` | Accounts ledger & settlements |
| `member@nur-e-haya.com` | `member` | VIP Member (5% discount everywhere) |
| `user@nur-e-haya.com` | `guest` | Regular guest user |

## Running Test Suites

Run all automated unit and integration suites:
```bash
python test_section_a.py
python test_section_b.py
python test_chatbot.py
python test_sections_e_to_l.py
python test_master_plan.py
```

## Production Deployment (Render)

1. Push to GitHub repository.
2. In Render dashboard, set Environment Variables:
   - `SECRET_KEY`: High-entropy 64-character hex string.
   - `FIREBASE_CREDENTIALS_JSON` or `FIREBASE_CREDENTIALS_BASE64`: Raw JSON or base64 string of service account key.
   - `FLASK_ENV`: `production`.
3. The included `render.yaml` and `Procfile` configure `web: PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python app.py`.
