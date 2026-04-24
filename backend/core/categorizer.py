"""
Expense Categorization Engine
Rule-based + keyword matching for transaction classification
"""

import re
from typing import Optional

CATEGORY_RULES = {
    "Food": [
        "restaurant", "cafe", "coffee", "pizza", "burger", "taco", "sushi",
        "mcdonald", "starbucks", "subway", "chipotle", "domino", "kfc",
        "uber eats", "doordash", "grubhub", "chick-fil-a", "panera",
        "dunkin", "wendy", "five guys", "taco bell", "olive garden",
        "texas roadhouse", "food", "diner", "grill", "kitchen", "bakery",
        "smoothie", "juice", "lunch", "dinner", "breakfast"
    ],
    "Transport": [
        "uber", "lyft", "taxi", "gas", "fuel", "shell", "exxon", "bp",
        "chevron", "parking", "toll", "metro", "subway ticket", "bus",
        "train", "flight", "airline", "transport", "ride", "auto"
    ],
    "Bills": [
        "electric", "electricity", "water", "gas bill", "internet",
        "phone", "rent", "mortgage", "insurance", "utility", "comcast",
        "at&t", "verizon", "t-mobile", "spectrum", "bill", "payment"
    ],
    "Shopping": [
        "amazon", "walmart", "target", "costco", "ebay", "etsy",
        "nike", "adidas", "h&m", "zara", "gap", "macy", "nordstrom",
        "best buy", "apple store", "mall", "shop", "store", "market",
        "whole foods", "trader joe", "kroger", "grocery"
    ],
    "Entertainment": [
        "netflix", "spotify", "hulu", "disney", "hbo", "youtube",
        "steam", "game", "cinema", "movie", "theater", "concert",
        "itunes", "playstation", "xbox", "twitch", "entertainment",
        "subscription", "prime"
    ],
    "Health": [
        "pharmacy", "cvs", "walgreens", "hospital", "clinic", "doctor",
        "dental", "dentist", "vision", "eye", "gym", "fitness",
        "health", "medical", "medicine", "drug", "vitamin", "wellness"
    ],
}

SUSPICIOUS_PATTERNS = [
    r"wire[_\s]transfer",
    r"unknown[_\s]merchant",
    r"offshore",
    r"crypto[_\s]",
    r"^[A-Z0-9_]{8,}$",  # All-caps random strings with underscores (e.g. UNKNOWN_XZ9)
]


def categorize_transaction(merchant: str, description: str = "", existing_category: str = "") -> str:
    """
    Categorize a transaction using rule-based keyword matching.
    Returns one of: Food, Transport, Bills, Shopping, Entertainment, Health, Others
    """
    if existing_category and existing_category.strip() and existing_category not in ["", "nan", "None"]:
        valid_cats = list(CATEGORY_RULES.keys()) + ["Others"]
        if existing_category in valid_cats:
            return existing_category

    text = f"{merchant} {description}".lower()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "Others"


def is_suspicious_merchant(merchant: str) -> bool:
    """Flag merchants that match suspicious patterns."""
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, merchant, re.IGNORECASE):
            return True
    return False


def categorize_dataframe(df):
    """Apply categorization to an entire transactions dataframe."""
    import pandas as pd

    df = df.copy()

    df["category"] = df.apply(
        lambda row: categorize_transaction(
            str(row.get("merchant", "")),
            str(row.get("description", "")),
            str(row.get("category", ""))
        ),
        axis=1
    )

    df["is_suspicious_merchant"] = df["merchant"].apply(
        lambda m: is_suspicious_merchant(str(m))
    )

    return df
