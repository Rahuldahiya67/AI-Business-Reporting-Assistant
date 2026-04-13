"""
Synthetic campaign dataset generator.
Produces 300 rows of ad campaign data across 5 channels, 5 products, 5 regions.
"""
import os
import json, random, csv
from datetime import date, timedelta

CHANNELS = ["Google Search", "Meta Ads", "Display Network", "YouTube", "LinkedIn"]
PRODUCTS = ["Analytics Pro", "Data Suite", "Cloud Connector", "BI Dashboard", "API Gateway"]
REGIONS  = ["North", "South", "East", "West", "Central"]

random.seed(42)

def rand_date(start="2024-01-01", days=365):
    base = date.fromisoformat(start)
    return (base + timedelta(days=random.randint(0, days))).isoformat()

def build_campaigns(n=300):
    rows = []
    for i in range(1, n + 1):
        spend   = round(random.uniform(500, 15_000), 2)
        clicks  = random.randint(200, 8_000)
        imps    = clicks * random.randint(10, 60)
        convs   = int(clicks * random.uniform(0.01, 0.08))
        revenue = round(convs * random.uniform(50, 500), 2)
        rows.append({
            "campaign_id"  : f"C{i:04d}",
            "campaign_date": rand_date(),
            "channel"      : random.choice(CHANNELS),
            "product"      : random.choice(PRODUCTS),
            "region"       : random.choice(REGIONS),
            "impressions"  : imps,
            "clicks"       : clicks,
            "spend"        : spend,
            "conversions"  : convs,
            "revenue"      : revenue,
        })
    return rows

if __name__ == "__main__":
    data = build_campaigns(300)
    os.makedirs("data", exist_ok=True)
    with open("data/campaigns.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=data[0].keys())
        w.writeheader(); w.writerows(data)
    with open("data/campaigns.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ Generated {len(data)} campaign records → data/campaigns.csv")

