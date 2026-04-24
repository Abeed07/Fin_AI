"""
Mock Transaction Data Generator
Generates realistic transaction data for testing without CSV upload
"""

import random
import pandas as pd
from datetime import datetime, timedelta


MOCK_MERCHANTS = {
    "Food": [
        ("Uber Eats", 15, 80), ("Starbucks", 5, 15), ("McDonald's", 8, 20),
        ("Chipotle", 12, 25), ("Domino's Pizza", 15, 45), ("Panera Bread", 10, 20),
        ("Chick-fil-A", 8, 18), ("Subway", 6, 12), ("Taco Bell", 5, 15)
    ],
    "Transport": [
        ("Uber", 8, 60), ("Lyft", 10, 50), ("Shell Gas", 30, 70),
        ("BP Gas Station", 25, 65), ("Metro Card", 10, 30)
    ],
    "Bills": [
        ("Electric Co", 80, 250), ("Internet Bill", 60, 150),
        ("Phone Bill", 40, 100), ("Rent Payment", 700, 1500)
    ],
    "Shopping": [
        ("Amazon", 15, 300), ("Walmart", 30, 150), ("Target", 25, 120),
        ("Costco", 50, 200), ("Nike Store", 40, 200), ("Zara", 30, 150)
    ],
    "Entertainment": [
        ("Netflix", 10, 20), ("Spotify", 10, 15), ("Steam", 5, 60),
        ("Hulu", 10, 18), ("Disney+", 8, 14), ("YouTube Premium", 12, 14)
    ],
    "Health": [
        ("CVS Pharmacy", 10, 80), ("Gym Membership", 25, 60),
        ("Doctor Visit", 30, 200), ("Dental Visit", 50, 300)
    ]
}

ANOMALY_MERCHANTS = [
    ("UNKNOWN_MERCHANT_XZ9", 500, 1200),
    ("WIRE_TRANSFER_INTL", 800, 2000),
    ("OFFSHORE_PAYMENT_CO", 300, 1000)
]


def generate_mock_transactions(months: int = 3, anomaly_rate: float = 0.03) -> pd.DataFrame:
    """Generate realistic mock transactions for the past N months."""
    transactions = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    current = start_date
    while current <= end_date:
        # 3-7 transactions per day
        n_txns = random.randint(0, 5)

        # Bills only once a month
        if current.day == 1:
            # Add rent and utility bills on the 1st
            for merchant, low, high in [("Rent Payment", 700, 1500), ("Electric Co", 80, 200)]:
                amount = round(random.uniform(low, high), 2)
                transactions.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "merchant": merchant,
                    "category": "Bills",
                    "description": f"{merchant} monthly payment"
                })

        for _ in range(n_txns):
            # Check if anomaly
            if random.random() < anomaly_rate:
                merchant_info = random.choice(ANOMALY_MERCHANTS)
                merchant, low, high = merchant_info
                amount = round(random.uniform(low, high), 2)
                category = "Others"
            else:
                category = random.choice(list(MOCK_MERCHANTS.keys()))
                merchant_info = random.choice(MOCK_MERCHANTS[category])
                merchant, low, high = merchant_info
                amount = round(random.uniform(low, high), 2)

            transactions.append({
                "date": current.strftime("%Y-%m-%d"),
                "amount": amount,
                "merchant": merchant,
                "category": category,
                "description": f"{merchant} purchase"
            })

        current += timedelta(days=1)

    df = pd.DataFrame(transactions)
    df = df.sort_values("date").reset_index(drop=True)
    return df
