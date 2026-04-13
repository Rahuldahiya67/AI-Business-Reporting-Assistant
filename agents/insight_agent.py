"""
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
        payload = f"User Query: {user_query}\n\nData Context:\n{json.dumps(context, indent=2, default=str)}"
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
