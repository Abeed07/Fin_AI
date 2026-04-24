FinanceIQ — AI Personal Finance & Spending Intelligence System

> Analyze transactions · Detect fraud · Get smart budget advice — all locally.

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│   index.html  ─  Chart.js  ─  Vanilla JS Dashboard             │
│   (Upload CSV / Load Demo → Display insights & anomalies)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST (CORS enabled)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                        │
│  POST /api/upload      GET /api/mock-data                       │
│  GET  /api/summary     GET /api/transactions                    │
│  GET  /api/insights    GET /api/anomalies                       │
│  GET  /api/budget-recommendations   GET /api/trends             │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             ▼                                ▼
┌────────────────────────┐    ┌───────────────────────────────────┐
│   CATEGORIZATION ENGINE│    │      ML ANOMALY DETECTOR          │
│   Rule-based keywords  │    │  Z-Score + IQR + Isolation Forest │
│   7 category taxonomy  │    │  Frequency spike detection        │
│   Suspicious merchant  │    │  Severity scoring (HIGH/MEDIUM)   │
│   pattern matching     │    │  Human-readable reasons           │
└────────────────────────┘    └───────────────────────────────────┘
             │                                │
             └──────────────┬─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INSIGHTS ENGINE                              │
│  Month-over-month comparisons  ·  Top spending categories       │
│  Daily/weekly trends  ·  Budget recommendations                 │
│  Savings opportunity identification  ·  Tips generation         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                  [Pandas DataFrame / In-memory]
                  (SQLite optional for persistence)
```

---
Folder Structure

```
finance_intelligence/
├── backend/
│   ├── main.py                    # FastAPI app & all routes
│   ├── requirements.txt           # Python dependencies
│   ├── core/
│   │   ├── categorizer.py         # Rule-based expense categorization
│   │   └── insights_engine.py     # Spending insights & budget recs
│   ├── ml/
│   │   └── anomaly_detector.py    # Z-score, IQR, Isolation Forest
│   └── data/
│       └── mock_generator.py      # Realistic mock transaction generator
├── frontend/
│   └── index.html                 # Complete dashboard (single file)
├── sample_data/
│   └── transactions.csv           # 90-day sample dataset (real-world like)
└── README.md                      # This file
```

---

Quick Start

Step 1: Prerequisites
```bash
# Python 3.9+ required
python --version
```

Step 2: Install Backend Dependencies
```bash
cd finance_intelligence/backend
pip install -r requirements.txt
```

Step 3: Start the Backend API
```bash
# From the backend/ directory
uvicorn main:app --reload --port 8000
```
You should see: `Uvicorn running on http://0.0.0.0:8000`

Step 4: Open the Frontend
```bash
# Option A: Just open in browser directly
open ../frontend/index.html

# Option B: Serve with Python (avoids some CORS issues)
cd ../frontend
python -m http.server 3000
# Then visit http://localhost:3000
```

 Step 5: Use the Dashboard
- Upload CSV: Click the upload zone or drag your `sample_data/transactions.csv`
- Demo Mode: Click "Load sample demo data" (backend must be running)

---

API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload CSV file |
| GET | `/api/mock-data` | Load simulated data |
| GET | `/api/transactions` | List transactions (paginated) |
| GET | `/api/summary` | Full dashboard data (one call) |
| GET | `/api/insights` | Month-over-month insights |
| GET | `/api/anomalies` | Flagged anomalies |
| GET | `/api/budget-recommendations` | Budget + savings plan |
| GET | `/api/trends` | Daily/weekly/monthly trends |

Interactive Docs: `http://localhost:8000/docs` (Swagger UI auto-generated)

---

CSV Format

Required columns:
```csv
date,amount,merchant,category,description
2024-01-15,45.50,Uber Eats,Food,Dinner delivery
2024-01-16,750.00,Rent Payment,,Monthly rent
```

- `date`: Any standard date format (YYYY-MM-DD preferred)
- `amount`: Positive number (expense amount)
- `merchant`: Merchant/payee name
- `category`: Optional — will be auto-detected if missing
- `description`: Optional — used for categorization hints

---

ML Models Used

| Model | Purpose | Library |
|-------|---------|---------|
| Z-Score | Large transaction detection | NumPy |
| IQR (Interquartile Range) | Spending outliers | Pandas |
| Isolation Forest | Multi-dimensional anomalies | scikit-learn |
| Frequency Analysis | Unusual spending spikes | Pandas |
| Rule-based NLP | Expense categorization | Python regex |

---

 Categories

| Category | Keywords Matched |
|----------|-----------------|
|Food | restaurants, delivery, coffee, fast food |
|Transport | uber, lyft, gas, parking, transit |
|Bills | electric, rent, internet, phone, insurance |
|Shopping | amazon, walmart, clothing stores |
|Entertainment | netflix, spotify, gaming, streaming |
|Health | pharmacy, doctor, gym, dental |
|Others | everything else |

---

