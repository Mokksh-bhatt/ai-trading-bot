from backend.traders.base import Trader, TraderDecision
from backend.models import MarketSnapshot

class HeuristicTrader(Trader):
    def decide(self, snapshot: MarketSnapshot, context: dict) -> TraderDecision:
        # Very basic heuristic for the baseline
        # Expects context to have some rolling stats, or falls back to basic logic
        
        action = "hold"
        reasoning = "No strong signal."
        confidence = 0.5
        
        avg_vol = context.get("avg_volume", snapshot.volume)
        if snapshot.volume > avg_vol * 1.2:
            action = "buy"
            reasoning = "Volume spike detected, initiating speculative buy."
            confidence = 0.8
        elif snapshot.volume < avg_vol * 0.8 and snapshot.volume > 0:
            action = "sell"
            reasoning = "Volume dropping, cutting exposure."
            confidence = 0.7
            
        return {
            "action": action, # type: ignore
            "size_pct": 10.0,
            "confidence": confidence,
            "reasoning": reasoning,
            "timeframe_tag": "intraday"
        }
