"""
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
        print("\n[Orchestrator] Starting agents...")
        self.data     = DataAgent()
        self.analyser = AnalysisAgent()
        self.insight  = InsightAgent(api_key=api_key)
        print("[Orchestrator] All agents ready.\n")

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
        print("\n" + "="*55)
        result = orc.ask(q)
        print("\n--- INSIGHT ---")
        print(result["insight"])
        print()
