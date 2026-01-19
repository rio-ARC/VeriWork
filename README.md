# Contribution Truth

> **"This system doesn't measure activity. It verifies truth."**

A web-based system that objectively analyzes and verifies individual contributions in college group projects using evidence, not self-reporting.

## 🎯 Core Feature: Claim Verification Engine

Students make contribution claims → **Gemini 3 autonomously tries to disprove them** using all available evidence.

This inversion is the key insight:
- Most tools count activity (commits, words, edits). That's trivial.
- We verify truth by attempting to disprove claims.

## Quick Start

### Prerequisites
- Python 3.11+
- Gemini API Key (set as `GEMINI_API_KEY` environment variable)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
Open `frontend/index.html` in your browser, or use a local server:
```bash
cd frontend
python -m http.server 8080
```

## Project Structure
```
├── backend/
│   ├── main.py              # FastAPI application
│   ├── api/                  # API routes and models
│   ├── ingestion/           # Data parsers
│   ├── analysis/            # Claim verification engine
│   └── tests/               # pytest tests
├── frontend/
│   ├── index.html           # Main UI
│   ├── css/                 # Styles
│   └── js/                  # Application logic
└── mock_data/               # Sample project data
```

## Verdicts
| Verdict | Meaning |
|---------|---------|
| ✅ VERIFIED | Claim supported by multiple evidence sources |
| ⚠️ DISPUTED | Counter-evidence found that contradicts claim |
| ❔ UNVERIFIABLE | Insufficient evidence to confirm or deny |

## Built for Gemini 3 Global Hackathon
