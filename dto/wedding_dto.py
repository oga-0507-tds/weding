from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class VenueDTO:
    """式場の基本情報を格納するDTO"""
    name: str
    detail_url: str

@dataclass
class CostDetailDTO:
    """個別の費用明細データを格納するDTO"""
    amount: int
    people_count: int
    wedding_date: str
    cost_type: str  # "本番" または "下見"
    detail_url: str

@dataclass
class CostSummaryDTO:
    """条件に合致した費用の集計結果を格納するDTO"""
    average_cost: Optional[float]
    matched_count: int
    details: List[CostDetailDTO] = field(default_factory=list)