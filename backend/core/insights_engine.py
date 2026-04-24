"""
Insights & Budget Recommendation Engine
Generates spending insights and personalized budget recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime


def compute_monthly_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute per-month, per-category spending totals."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    summary = df.groupby(["month", "category"])["amount"].sum().reset_index()
    summary["month"] = summary["month"].astype(str)
    return summary


def get_spending_insights(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate month-over-month insights and trends."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    monthly = df.groupby(["month", "category"])["amount"].sum().unstack(fill_value=0)
    monthly.index = monthly.index.astype(str)

    months = sorted(monthly.index.tolist())
    insights = []
    category_changes = {}

    if len(months) >= 2:
        prev_month = months[-2]
        curr_month = months[-1]

        for category in monthly.columns:
            prev = monthly.loc[prev_month, category] if prev_month in monthly.index else 0
            curr = monthly.loc[curr_month, category] if curr_month in monthly.index else 0

            if prev > 0:
                pct_change = ((curr - prev) / prev) * 100
                category_changes[category] = round(pct_change, 1)

                if abs(pct_change) >= 10:
                    direction = "more" if pct_change > 0 else "less"
                    emoji = "📈" if pct_change > 0 else "📉"
                    insights.append({
                        "type": "month_comparison",
                        "category": category,
                        "message": f"{emoji} You spent {abs(pct_change):.0f}% {direction} on {category} compared to last month (${curr:.0f} vs ${prev:.0f})",
                        "change_pct": round(pct_change, 1),
                        "current": round(curr, 2),
                        "previous": round(prev, 2)
                    })

    # Top spending categories this month
    if months:
        latest = months[-1]
        if latest in monthly.index:
            top_cats = monthly.loc[latest].sort_values(ascending=False).head(3)
            top_list = [{"category": cat, "amount": round(amt, 2)} for cat, amt in top_cats.items() if amt > 0]
            insights.append({
                "type": "top_categories",
                "message": f"🏆 Your top 3 spending categories this month: {', '.join([c['category'] for c in top_list])}",
                "categories": top_list
            })

    # Daily average spending
    total_days = (df["date"].max() - df["date"].min()).days + 1
    daily_avg = df["amount"].sum() / max(total_days, 1)
    insights.append({
        "type": "daily_average",
        "message": f"📊 Your average daily spending is ${daily_avg:.2f}",
        "daily_avg": round(daily_avg, 2)
    })

    return {
        "insights": insights,
        "category_changes": category_changes,
        "months_analyzed": months
    }


def get_budget_recommendations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate budget recommendations based on historical spending."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Monthly averages per category
    df["month"] = df["date"].dt.to_period("M")
    monthly_cat = df.groupby(["month", "category"])["amount"].sum().reset_index()
    avg_by_cat = monthly_cat.groupby("category")["amount"].mean()

    recommendations = []

    # Recommended budget = 90% of average (10% savings target)
    SAVINGS_TARGETS = {
        "Food": 0.15,       # 15% reduction opportunity
        "Entertainment": 0.20,
        "Shopping": 0.15,
        "Transport": 0.10,
        "Health": 0.0,      # Don't suggest cutting health
        "Bills": 0.05,
        "Others": 0.25
    }

    total_monthly = avg_by_cat.sum()

    for category, avg_spend in avg_by_cat.items():
        savings_pct = SAVINGS_TARGETS.get(category, 0.10)
        recommended = avg_spend * (1 - savings_pct)
        potential_savings = avg_spend - recommended
        pct_of_total = (avg_spend / total_monthly * 100) if total_monthly > 0 else 0

        rec = {
            "category": category,
            "avg_monthly_spend": round(float(avg_spend), 2),
            "recommended_budget": round(float(recommended), 2),
            "potential_savings": round(float(potential_savings), 2),
            "savings_pct": int(savings_pct * 100),
            "pct_of_total": round(float(pct_of_total), 1)
        }

        # Add specific tips
        if category == "Food" and avg_spend > 200:
            rec["tip"] = f"💡 You can save ${potential_savings:.0f}/month by cooking at home 3x per week"
        elif category == "Entertainment" and avg_spend > 100:
            rec["tip"] = f"💡 Review subscriptions — you could save ${potential_savings:.0f}/month by cutting unused services"
        elif category == "Shopping" and avg_spend > 150:
            rec["tip"] = f"💡 Try a 48-hour rule before purchases to save ~${potential_savings:.0f}/month"
        elif category == "Transport" and avg_spend > 100:
            rec["tip"] = f"💡 Carpooling or public transit could save ${potential_savings:.0f}/month"
        else:
            rec["tip"] = f"💡 Target ${recommended:.0f}/month to save ${potential_savings:.0f}"

        recommendations.append(rec)

    # Sort by potential savings descending
    recommendations.sort(key=lambda x: x["potential_savings"], reverse=True)

    total_savings = sum(r["potential_savings"] for r in recommendations)

    return {
        "recommendations": recommendations,
        "total_monthly_spend": round(float(total_monthly), 2),
        "total_potential_savings": round(float(total_savings), 2),
        "annual_savings_potential": round(float(total_savings * 12), 2)
    }


def get_spending_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """Daily and weekly spending trends for charts."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Daily totals
    daily = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
    daily.columns = ["date", "total"]
    daily["date"] = daily["date"].astype(str)

    # Weekly totals
    df["week"] = df["date"].dt.to_period("W")
    weekly = df.groupby("week")["amount"].sum().reset_index()
    weekly["week"] = weekly["week"].astype(str)

    # Category breakdown (latest month)
    df["month"] = df["date"].dt.to_period("M")
    latest_month = df["month"].max()
    latest_df = df[df["month"] == latest_month]
    cat_breakdown = latest_df.groupby("category")["amount"].sum().reset_index()
    cat_breakdown.columns = ["category", "amount"]
    cat_breakdown["amount"] = cat_breakdown["amount"].round(2)

    # Monthly totals for trend line
    monthly_totals = df.groupby("month")["amount"].sum().reset_index()
    monthly_totals["month"] = monthly_totals["month"].astype(str)

    return {
        "daily": daily.to_dict(orient="records"),
        "weekly": weekly.to_dict(orient="records"),
        "category_breakdown": cat_breakdown.to_dict(orient="records"),
        "monthly_totals": monthly_totals.to_dict(orient="records")
    }
