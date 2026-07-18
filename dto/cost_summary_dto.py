from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class CostSummaryDTO:
    average_cost: int
    matched_count: int
    target_urls: List[str]