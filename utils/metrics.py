"""
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
