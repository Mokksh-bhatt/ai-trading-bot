from typing import Protocol, Literal, TypedDict
from backend.models import MarketSnapshot

class TraderDecision(TypedDict):
    action: Literal["buy", "sell", "hold"]
    size_pct: float          # % of paper capital allocated
    confidence: float        # 0-1
    reasoning: str           # model's stated rationale
    timeframe_tag: Literal["scalp", "intraday", "swing", "long_hold"]

class Trader(Protocol):
    def decide(self, snapshot: MarketSnapshot, context: dict) -> TraderDecision:
        ...
