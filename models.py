# models.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class ExecutionMode(str, Enum):
    PAPER = "paper"
    ALERT = "alert"
    LIVE = "live"

@dataclass
class Signal:
    strategy: str
    symbol: str
    side: Side
    qty: int
    exchange: str = "NSE"
    token: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    meta: dict = field(default_factory=dict)

@dataclass
class Trade:
    trade_id: str
    strategy: str
    symbol: str
    side: Side
    qty: int
    entry_price: float
    entry_time: datetime
    status: TradeStatus = TradeStatus.OPEN
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    meta: dict = field(default_factory=dict)
