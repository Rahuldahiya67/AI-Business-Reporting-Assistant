"""
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
