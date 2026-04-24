"""
AI Personal Finance Intelligence System - FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

import io
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.categorizer import categorize_dataframe
from core.insights_engine import (
    get_spending_insights,
    get_budget_recommendations,
    get_spending_trends,
    compute_monthly_summary
)
from ml.anomaly_detector import detect_all_anomalies, get_anomaly_summary
from data.mock_generator import generate_mock_transactions

app = FastAPI(
    title="Personal Finance Intelligence API",
    description="AI-powered spending analysis, anomaly detection & budget recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use SQLite for persistence)
_current_df = None


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Full processing pipeline: categorize → detect anomalies."""
    required_cols = {"date", "amount", "merchant"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    df = df.sort_values("date").reset_index(drop=True)

    df = categorize_dataframe(df)
    df = detect_all_anomalies(df)

    return df


@app.get("/")
def root():
    return {"message": "Personal Finance Intelligence API is running 🚀", "version": "1.0.0"}


@app.post("/api/upload")
async def upload_transactions(file: UploadFile = File(...)):
    """Upload a CSV file of bank transactions."""
    global _current_df

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        _current_df = process_dataframe(df)

        return {
            "success": True,
            "total_transactions": len(_current_df),
            "date_range": {
                "start": str(_current_df["date"].min().date()),
                "end": str(_current_df["date"].max().date())
            },
            "total_amount": round(float(_current_df["amount"].sum()), 2),
            "categories": _current_df["category"].value_counts().to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@app.get("/api/mock-data")
def load_mock_data(months: int = 3):
    """Load simulated transaction data for demo purposes."""
    global _current_df

    try:
        df = generate_mock_transactions(months=months)
        _current_df = process_dataframe(df)

        return {
            "success": True,
            "total_transactions": len(_current_df),
            "date_range": {
                "start": str(_current_df["date"].min().date()),
                "end": str(_current_df["date"].max().date())
            },
            "total_amount": round(float(_current_df["amount"].sum()), 2),
            "categories": _current_df["category"].value_counts().to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions")
def get_transactions(limit: int = 100, offset: int = 0):
    """Get paginated list of transactions."""
    if _current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded. Upload CSV or use /api/mock-data first.")

    df = _current_df.copy()
    df["date"] = df["date"].astype(str)

    # Replace NaN with None for JSON serialization
    df = df.where(pd.notnull(df), None)

    total = len(df)
    page_df = df.iloc[offset:offset + limit]

    records = []
    for _, row in page_df.iterrows():
        records.append({
            "date": row["date"],
            "amount": float(row["amount"]),
            "merchant": str(row.get("merchant", "")),
            "category": str(row.get("category", "Others")),
            "description": str(row.get("description", "")),
            "is_anomaly": bool(row.get("is_anomaly", False)),
            "anomaly_reason": str(row.get("anomaly_reason", ""))
        })

    return {"total": total, "offset": offset, "limit": limit, "transactions": records}


@app.get("/api/insights")
def get_insights():
    """Get spending insights and month-over-month comparisons."""
    if _current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")
    try:
        return get_spending_insights(_current_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anomalies")
def get_anomalies():
    """Get list of flagged anomalous transactions."""
    if _current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")
    try:
        anomalies = get_anomaly_summary(_current_df)
        return {
            "total_anomalies": len(anomalies),
            "anomalies": anomalies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/budget-recommendations")
def get_budget_recs():
    """Get personalized budget recommendations."""
    if _current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")
    try:
        return get_budget_recommendations(_current_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends")
def get_trends():
    """Get spending trends data for charts."""
    if _current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")
    try:
        return get_spending_trends(_current_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary")
def get_summary():
    """Get complete dashboard summary in one call."""
    if _current_df is None:
        raise HTTPException(status_code=404, detail="No data loaded.")
    try:
        df = _current_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        latest_month = df["date"].dt.to_period("M").max()
        latest_df = df[df["date"].dt.to_period("M") == latest_month]

        return {
            "overview": {
                "total_transactions": len(df),
                "total_spend": round(float(df["amount"].sum()), 2),
                "current_month_spend": round(float(latest_df["amount"].sum()), 2),
                "avg_transaction": round(float(df["amount"].mean()), 2),
                "anomaly_count": int(df["is_anomaly"].sum()),
                "date_range": {
                    "start": str(df["date"].min().date()),
                    "end": str(df["date"].max().date())
                }
            },
            "trends": get_spending_trends(df),
            "insights": get_spending_insights(df),
            "anomalies": get_anomaly_summary(df)[:5],
            "budget": get_budget_recommendations(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
