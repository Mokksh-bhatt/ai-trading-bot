from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class MarketSnapshot(BaseModel):
    symbol: str
    asset_class: Literal["stock", "crypto"]
    price: float
    volume: float
    timestamp: datetime
    context: Optional[dict] = None

class TradeRecord(BaseModel):
    model_name: str
    strategy_tag: str
    asset_class: str
    symbol: str
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl_pct: Optional[float] = None
    reasoning_text: str
    confidence: float
