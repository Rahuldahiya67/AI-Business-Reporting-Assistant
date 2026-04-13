"""
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
