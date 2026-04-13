"""
run_setup.py  —  Run this ONE file to build the entire project.
Just place this file anywhere and run: python run_setup.py
"""

import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

print("\n" + "="*55)
print("   AI Business Reporting Assistant — Auto Setup")
print("="*55)

# ── 1. Create folder structure ────────────────────────────────
print("\n[1/5] Creating folder structure...")
folders = ["agents", "data", "sql", "utils"]
for f in folders:
    os.makedirs(f, exist_ok=True)
    init = os.path.join(f, "__init__.py")
    if not os.path.exists(init):
        open(init, "w").close()
print("      ✓ Folders ready")

# ── 2. Write all source files ─────────────────────────────────
print("\n[2/5] Writing project files...")

files = {}

# ── generate_data.py ──────────────────────────────────────────
files["data/generate_data.py"] = '''"""
Synthetic campaign dataset generator.
Produces 300 rows of ad campaign data across 5 channels, 5 products, 5 regions.
"""
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

import os
'''

# ── metrics.py ────────────────────────────────────────────────
files["utils/metrics.py"] = '''"""
Core KPI computation engine.
Calculates CPC, CPM, ROAS, CTR, CVR, CPA from raw campaign data.
"""
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class CampaignMetrics:
    campaign_id : str
    channel     : str
    product     : str
    region      : str
    spend       : float
    revenue     : float
    clicks      : int
    impressions : int
    conversions : int

    @property
    def cpc(self):   return round(self.spend / self.clicks, 4) if self.clicks else 0.0
    @property
    def cpm(self):   return round((self.spend / self.impressions) * 1000, 4) if self.impressions else 0.0
    @property
    def roas(self):  return round(self.revenue / self.spend, 4) if self.spend else 0.0
    @property
    def ctr(self):   return round((self.clicks / self.impressions) * 100, 4) if self.impressions else 0.0
    @property
    def cvr(self):   return round((self.conversions / self.clicks) * 100, 4) if self.clicks else 0.0
    @property
    def cpa(self):   return round(self.spend / self.conversions, 4) if self.conversions else 0.0
    @property
    def profit(self):return round(self.revenue - self.spend, 2)

    def to_dict(self):
        return {k: getattr(self, k) for k in
                ["campaign_id","channel","product","region","spend","revenue",
                 "clicks","impressions","conversions","cpc","cpm","roas","ctr","cvr","cpa","profit"]}

def aggregate_by(records: List[CampaignMetrics], key: str) -> List[Dict]:
    buckets = {}
    for r in records:
        dim = getattr(r, key)
        if dim not in buckets:
            buckets[dim] = {"spend":0,"revenue":0,"clicks":0,"impressions":0,"conversions":0,"count":0}
        b = buckets[dim]
        b["spend"] += r.spend; b["revenue"] += r.revenue; b["clicks"] += r.clicks
        b["impressions"] += r.impressions; b["conversions"] += r.conversions; b["count"] += 1

    result = []
    for dim, b in buckets.items():
        sp = b["spend"] or 1; cl = b["clicks"] or 1; im = b["impressions"] or 1; cv = b["conversions"] or 1
        result.append({key: dim, "spend": round(b["spend"],2), "revenue": round(b["revenue"],2),
                       "roas": round(b["revenue"]/sp,3), "cpc": round(b["spend"]/cl,3),
                       "cpm": round((b["spend"]/im)*1000,3), "cpa": round(b["spend"]/cv,3),
                       "profit": round(b["revenue"]-b["spend"],2), "campaigns": b["count"]})
    return sorted(result, key=lambda x: x["roas"], reverse=True)
'''

# ── data_agent.py ─────────────────────────────────────────────
files["agents/data_agent.py"] = '''"""
Data Agent — loads campaign CSV into SQLite and exposes query methods.
All other agents talk through this layer only.
"""
import sqlite3, csv, re
from pathlib import Path
from typing import List, Dict, Any

class DataAgent:
    def __init__(self, csv_path: str = "data/campaigns.csv"):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self._ingest(csv_path)
        self._create_views()

    def _ingest(self, path: str):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE campaigns (
                campaign_id TEXT, campaign_date TEXT, channel TEXT,
                product TEXT, region TEXT, impressions INTEGER,
                clicks INTEGER, spend REAL, conversions INTEGER, revenue REAL
            )""")
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            rows = [(r["campaign_id"], r["campaign_date"], r["channel"], r["product"],
                     r["region"], int(r["impressions"]), int(r["clicks"]),
                     float(r["spend"]), int(r["conversions"]), float(r["revenue"]))
                    for r in reader]
        cur.executemany("INSERT INTO campaigns VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
        self.conn.commit()
        print(f"  ✓ DataAgent loaded {len(rows)} records into memory")

    def _create_views(self):
        sql_file = Path("sql/queries.sql")
        if not sql_file.exists(): return
        raw = sql_file.read_text()
        for stmt in [s.strip() for s in re.split(r"(?=CREATE VIEW)", raw) if s.strip()]:
            try: self.conn.execute(stmt)
            except: pass
        self.conn.commit()

    def run_sql(self, query: str) -> List[Dict[str, Any]]:
        cur  = self.conn.execute(query)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def summary(self):        return self.run_sql("SELECT * FROM v_summary")[0]
    def by_channel(self):     return self.run_sql("SELECT * FROM v_by_channel")
    def by_product(self):     return self.run_sql("SELECT * FROM v_by_product")
    def by_region(self):      return self.run_sql("SELECT * FROM v_by_region")
    def monthly_trend(self):  return self.run_sql("SELECT * FROM v_monthly_trend")
    def top_roas(self):       return self.run_sql("SELECT * FROM v_top_roas")
    def underperformers(self):return self.run_sql("SELECT * FROM v_underperformers")
'''

# ── analysis_agent.py ─────────────────────────────────────────
files["agents/analysis_agent.py"] = '''"""
Analysis Agent — enriches raw data with rankings, anomaly flags, trend deltas.
Pure deterministic Python — no LLM calls here.
"""
import statistics
from typing import List, Dict, Any

class AnalysisAgent:

    def rank_channels(self, data: List[Dict]) -> List[Dict]:
        sorted_rows = sorted(data, key=lambda r: r["roas"], reverse=True)
        for i, row in enumerate(sorted_rows):
            row["rank"] = i + 1
            row["tier"] = self._tier(row["roas"])
        return sorted_rows

    def detect_anomalies(self, rows: List[Dict], metric: str = "roas") -> List[Dict]:
        vals = [r[metric] for r in rows if metric in r]
        if len(vals) < 3: return []
        mu, sigma = statistics.mean(vals), statistics.stdev(vals)
        flagged = []
        for row in rows:
            val = row.get(metric, 0)
            if abs(val - mu) > 1.5 * sigma:
                direction = "above" if val > mu else "below"
                flagged.append({**row, "anomaly": f"{direction} avg by {round(abs(val-mu),2)}"})
        return flagged

    def compute_trend_delta(self, monthly: List[Dict]) -> List[Dict]:
        enriched = []
        for i, row in enumerate(monthly):
            row = dict(row)
            prev = monthly[i-1] if i > 0 else None
            row["revenue_delta"] = round(row["revenue"] - prev["revenue"], 2) if prev else None
            row["spend_delta"]   = round(row["spend"]   - prev["spend"],   2) if prev else None
            row["roas_delta"]    = round(row["roas"]    - prev["roas"],    3) if prev else None
            enriched.append(row)
        return enriched

    def budget_efficiency(self, data: List[Dict]) -> Dict[str, Any]:
        ranked = sorted(data, key=lambda r: r["roas"], reverse=True)
        best, worst = ranked[0], ranked[-1]
        total_sp  = sum(r["spend"] for r in data)
        total_rev = sum(r["revenue"] for r in data)
        return {
            "best_channel" : best.get("channel"),  "best_roas" : best.get("roas"),
            "worst_channel": worst.get("channel"), "worst_roas": worst.get("roas"),
            "total_spend"  : round(total_sp, 2),   "total_revenue": round(total_rev, 2),
            "overall_roas" : round(total_rev / total_sp, 3) if total_sp else 0,
        }

    @staticmethod
    def _tier(roas: float) -> str:
        if roas >= 4.0: return "Elite"
        if roas >= 2.5: return "Strong"
        if roas >= 1.5: return "Average"
        return "Underperforming"
'''

# ── insight_agent.py ──────────────────────────────────────────
files["agents/insight_agent.py"] = '''"""
Insight Agent — sends enriched data to Claude API and returns NL insights.
Falls back to rule-based summary if no API key is set.
"""
import json, os
from typing import Dict, Any

try:
    import anthropic
    _SDK = True
except ImportError:
    _SDK = False

SYSTEM_PROMPT = """
You are a senior business intelligence analyst specialising in digital advertising.
Turn structured campaign metrics into concise, executive-ready insights.

Rules:
- Lead with the most important finding, not background.
- Every insight must include a concrete, actionable recommendation.
- Use specific numbers from the data — never speak in vague generalities.
- Structure output as:
    ## Key Finding
    ## What is Working
    ## What Needs Attention
    ## Recommended Actions (numbered list)
    ## ROI Optimisation Tip
""".strip()

class InsightAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.client  = anthropic.Anthropic(api_key=self.api_key) if (_SDK and self.api_key) else None

    def generate_insight(self, context: Dict[str, Any], user_query: str) -> str:
        payload = f"User Query: {user_query}\\n\\nData Context:\\n{json.dumps(context, indent=2, default=str)}"
        if self.client:
            msg = self.client.messages.create(
                model="claude-opus-4-5", max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": payload}]
            )
            return msg.content[0].text
        return self._fallback(context)

    def _fallback(self, ctx: Dict) -> str:
        s  = ctx.get("summary", {})
        ch = ctx.get("channels", [])
        best = ch[0] if ch else {}
        return f"""## Key Finding
Total spend of ${s.get("total_spend",0):,.0f} generated ${s.get("total_revenue",0):,.0f} revenue (ROAS = {s.get("overall_roas",0)}).

## What is Working
{best.get("channel","N/A")} leads all channels with ROAS of {best.get("roas",0)}.

## What Needs Attention
Channels with ROAS below 1.5 are losing money. Immediate budget review recommended.

## Recommended Actions
1. Reallocate 20% of spend from underperforming channels to {best.get("channel","top channel")}.
2. A/B test creative on channels with high impressions but low CTR.
3. Set a hard ROAS floor of 1.8 before approving new campaign budgets.

## ROI Optimisation Tip
Prioritise campaigns with CPA below your average customer LTV.
Campaigns with high CPA but strong CVR signal product-market fit — reduce CPMs by refining audience targeting."""
'''

# ── queries.sql ───────────────────────────────────────────────
files["sql/queries.sql"] = """-- Business Reporting Assistant — SQL Views

CREATE VIEW IF NOT EXISTS v_summary AS
SELECT
    COUNT(DISTINCT campaign_id)                                    AS total_campaigns,
    ROUND(SUM(spend), 2)                                           AS total_spend,
    ROUND(SUM(revenue), 2)                                         AS total_revenue,
    ROUND(SUM(revenue) - SUM(spend), 2)                            AS total_profit,
    SUM(clicks)                                                    AS total_clicks,
    SUM(impressions)                                               AS total_impressions,
    SUM(conversions)                                               AS total_conversions,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS overall_roas,
    ROUND(SUM(spend)   / NULLIF(SUM(clicks), 0), 3)                AS avg_cpc,
    ROUND(SUM(spend)   / NULLIF(SUM(impressions), 0) * 1000, 3)    AS avg_cpm,
    ROUND(SUM(spend)   / NULLIF(SUM(conversions), 0), 3)           AS avg_cpa
FROM campaigns;

CREATE VIEW IF NOT EXISTS v_by_channel AS
SELECT channel,
    COUNT(*)                                                       AS num_campaigns,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) - SUM(spend), 2)                            AS profit,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas,
    ROUND(SUM(spend)   / NULLIF(SUM(clicks), 0), 3)                AS cpc,
    ROUND(SUM(spend)   / NULLIF(SUM(impressions), 0) * 1000, 3)    AS cpm,
    ROUND(SUM(spend)   / NULLIF(SUM(conversions), 0), 3)           AS cpa
FROM campaigns GROUP BY channel ORDER BY roas DESC;

CREATE VIEW IF NOT EXISTS v_by_product AS
SELECT product,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas,
    ROUND(SUM(spend)   / NULLIF(SUM(conversions), 0), 3)           AS cpa,
    SUM(conversions)                                               AS conversions
FROM campaigns GROUP BY product ORDER BY revenue DESC;

CREATE VIEW IF NOT EXISTS v_by_region AS
SELECT region,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas
FROM campaigns GROUP BY region ORDER BY revenue DESC;

CREATE VIEW IF NOT EXISTS v_monthly_trend AS
SELECT STRFTIME('%Y-%m', campaign_date)                            AS month,
    ROUND(SUM(spend), 2)                                           AS spend,
    ROUND(SUM(revenue), 2)                                         AS revenue,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 3)                 AS roas,
    SUM(conversions)                                               AS conversions
FROM campaigns GROUP BY month ORDER BY month;

CREATE VIEW IF NOT EXISTS v_top_roas AS
SELECT campaign_id, channel, product, region,
    ROUND(spend, 2)                                                AS spend,
    ROUND(revenue, 2)                                              AS revenue,
    ROUND(revenue / NULLIF(spend, 0), 3)                           AS roas,
    ROUND(spend   / NULLIF(conversions, 0), 3)                     AS cpa,
    conversions
FROM campaigns ORDER BY roas DESC LIMIT 10;

CREATE VIEW IF NOT EXISTS v_underperformers AS
SELECT campaign_id, channel, product,
    ROUND(spend, 2)                                                AS spend,
    ROUND(revenue / NULLIF(spend, 0), 3)                           AS roas,
    ROUND(revenue - spend, 2)                                      AS profit_loss
FROM campaigns WHERE (revenue / NULLIF(spend, 0)) < 1.5
ORDER BY profit_loss ASC;
"""

# ── orchestrator.py ───────────────────────────────────────────
files["orchestrator.py"] = '''"""
Orchestrator — the agentic workflow controller.
Runs: Plan → Fetch → Analyse → Insight for every user query.

Usage:
    python orchestrator.py
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.data_agent     import DataAgent
from agents.analysis_agent import AnalysisAgent
from agents.insight_agent  import InsightAgent

INTENT_MAP = {
    "channel"      : ["channel","platform","google","meta","linkedin","youtube","display"],
    "product"      : ["product","suite","connector","gateway","analytics","dashboard"],
    "region"       : ["region","north","south","east","west","central","geography"],
    "trend"        : ["trend","month","time","growth","over time","period"],
    "top"          : ["top","best","highest","roas","winner","leading"],
    "underperform" : ["worst","underperform","low","losing","poor","weak"],
    "summary"      : ["summary","overview","total","overall","how are we"],
}

def detect_intent(query: str) -> str:
    q = query.lower()
    for intent, keywords in INTENT_MAP.items():
        if any(kw in q for kw in keywords):
            return intent
    return "summary"

class Orchestrator:
    def __init__(self, api_key: str = None):
        print("\\n[Orchestrator] Starting agents...")
        self.data     = DataAgent()
        self.analyser = AnalysisAgent()
        self.insight  = InsightAgent(api_key=api_key)
        print("[Orchestrator] All agents ready.\\n")

    def ask(self, query: str) -> dict:
        print(f"  Query  : {query}")
        intent  = detect_intent(query)
        print(f"  Intent : {intent}")
        raw     = self._fetch(intent)
        analysis= self._analyse(intent, raw)
        context = {"intent": intent, "summary": self.data.summary(),
                   "channels": self.data.by_channel(), "analysis": analysis}
        result  = self.insight.generate_insight(context, query)
        return {"query": query, "intent": intent, "analysis": analysis, "insight": result}

    def _fetch(self, intent):
        fn = {"channel": self.data.by_channel, "product": self.data.by_product,
              "region" : self.data.by_region,  "trend"  : self.data.monthly_trend,
              "top"    : self.data.top_roas,    "underperform": self.data.underperformers,
              "summary": self.data.summary}.get(intent, self.data.summary)
        data = fn()
        return data if isinstance(data, list) else [data]

    def _analyse(self, intent, raw):
        if intent == "channel":
            return {"ranked": self.analyser.rank_channels(raw),
                    "anomalies": self.analyser.detect_anomalies(raw, "roas"),
                    "budget": self.analyser.budget_efficiency(raw)}
        if intent == "trend":
            return {"trend": self.analyser.compute_trend_delta(raw)}
        return {"data": raw}


if __name__ == "__main__":
    orc = Orchestrator()

    test_queries = [
        "How are we doing overall?",
        "Which channel has the best ROAS?",
        "Show me monthly revenue trends",
        "Which campaigns are underperforming?",
        "Which product generates the most revenue?",
    ]

    for q in test_queries:
        print("\\n" + "="*55)
        result = orc.ask(q)
        print("\\n--- INSIGHT ---")
        print(result["insight"])
        print()
'''

# ── .gitignore ────────────────────────────────────────────────
files[".gitignore"] = """venv/
__pycache__/
*.pyc
*.pyo
.env
data/campaigns.csv
data/campaigns.json
.DS_Store
*.egg-info/
dist/
build/
"""

# ── requirements.txt ──────────────────────────────────────────
files["requirements.txt"] = "anthropic>=0.25.0\n"

# ── Write all files ───────────────────────────────────────────
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"      ✓ {path}")

print("\n[3/5] Installing dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "anthropic", "-q"], check=False)
print("      ✓ anthropic installed")

print("\n[4/5] Generating dataset...")
exec(open("data/generate_data.py").read().replace(
    "import os", "import os, csv, json, random\nfrom datetime import date, timedelta"
).split("import os")[-1] if False else "")
subprocess.run([sys.executable, "data/generate_data.py"], check=True)

print("\n[5/5] Running the assistant...")
print("-"*55)
subprocess.run([sys.executable, "orchestrator.py"], check=True)

print("\n" + "="*55)
print("   SETUP COMPLETE!")
print("="*55)
print("""
 Next steps:
   1. Run the assistant anytime:
      python orchestrator.py

   2. Add your Anthropic API key for real AI insights:
      Create a .env file and add:
      ANTHROPIC_API_KEY=sk-ant-your-key-here

   3. Push to GitHub:
      git init
      git add .
      git commit -m "feat: AI business reporting assistant"
      git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
      git push -u origin main
""")
