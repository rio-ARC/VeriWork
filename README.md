# VeriWork

> **Evidence-Backed Contribution Verification for Group Projects**

🔗 **Live Demo**: [Frontend](YOUR_VERCEL_URL_HERE) | [API](YOUR_RENDER_URL_HERE)

---

## 🎯 What is VeriWork?

VeriWork is an AI-powered system that **verifies individual contributions** in group projects using evidence—not self-reporting.

**The Problem**: In college group projects, it's nearly impossible to know who actually did the work. Students can claim credit for contributions they didn't make.

**Our Solution**: VeriWork analyzes git logs and meeting transcripts to **verify or dispute** contribution claims. Instead of measuring activity, it attempts to **disprove** claims. If disproval fails, the claim is likely true.

---

## ⚡ The Core Innovation: Disproval-Based Verification

Most tools count commits or lines of code. VeriWork does something different:

```
Student claims: "I implemented the authentication system"
                        ↓
Gemini AI tries to DISPROVE it using all evidence
                        ↓
VERDICT: ✅ VERIFIED | ⚠️ DISPUTED | ❔ UNVERIFIABLE
```

### How It Works

1. **Upload Evidence**: Git logs + meeting transcripts
2. **Submit a Claim**: "Alice says she built the login system"
3. **AI Analysis**: Gemini searches for counter-evidence:
   - Are there commits from Alice touching auth files?
   - Did someone ELSE write that code?
   - Did Alice discuss this in meetings?
4. **Verdict**: Evidence-backed result with citations

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **AI** | Google Gemini 2.0 Flash |
| **Backend** | FastAPI (Python) |
| **Frontend** | Vanilla JS + CSS (Glassmorphism UI) |
| **Data Models** | Pydantic |
| **Testing** | pytest (30 tests) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Gemini API Key ([Get one free](https://aistudio.google.com/app/apikey))

### Run Locally

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/veriwork.git
cd veriwork

# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
$env:GEMINI_API_KEY = "your_api_key"
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
python -m http.server 3000
```

Open: **http://localhost:3000**

---

## 📁 Project Structure

```
veriwork/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── api/
│   │   ├── routes.py           # REST endpoints
│   │   └── models.py           # Pydantic schemas
│   ├── ingestion/
│   │   ├── git_parser.py       # Parses git logs
│   │   └── transcript_parser.py
│   ├── analysis/
│   │   ├── gemini_client.py    # Gemini API wrapper
│   │   └── claim_verifier.py   # THE CORE ENGINE
│   └── tests/                  # 30 pytest tests
├── frontend/
│   ├── index.html
│   ├── css/                    # Glassmorphism theme
│   └── js/                     # App logic
└── mock_data/                  # Sample data for testing
```

---

## 📊 Example Verdicts

### ⚠️ DISPUTED
> **Claim**: "Alice implemented the entire authentication system"  
> **Evidence**: Git shows 1 typo fix from Alice; Bob authored 523 lines of auth code  
> **Confidence**: 85%

### ✅ VERIFIED
> **Claim**: "Bob designed and built the auth system"  
> **Evidence**: 5 commits to auth/, presented architecture in sprint meeting  
> **Confidence**: 92%

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check API status |
| `/api/evidence/upload` | POST | Upload git log + transcript |
| `/api/verify` | POST | Verify a contribution claim |
| `/api/evidence/status` | GET | Check uploaded evidence |

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
# ======================== 30 passed ========================
```

---

## 🌐 Deployment

| Component | Platform | URL |
|-----------|----------|-----|
| Frontend | Vercel | [YOUR_VERCEL_URL_HERE](YOUR_VERCEL_URL_HERE) |
| Backend | Render | [YOUR_RENDER_URL_HERE](YOUR_RENDER_URL_HERE) |

---

## 📄 License

MIT License
