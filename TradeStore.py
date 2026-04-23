from threading import RLock
from typing import Dict, List, Optional, Tuple

from models import Trade, TradeStatus


class LiveTradeStore:
    def __init__(self):
        self._lock = RLock()
        self._trades: Dict[str, Trade] = {}
        self._open_by_key: Dict[Tuple[str, str], str] = {}

    def add_trade(self, trade: Trade) -> None:
        with self._lock:
            key = (trade.strategy, trade.symbol)
            if trade.status == TradeStatus.OPEN and key in self._open_by_key:
                raise ValueError(f"Open trade already exists for strategy-symbol: {key}")

            self._trades[trade.trade_id] = trade
            if trade.status == TradeStatus.OPEN:
                self._open_by_key[key] = trade.trade_id

    def update_trade(self, trade_id: str, **updates) -> Trade:
        with self._lock:
            trade = self._trades[trade_id]
            for field_name, value in updates.items():
                setattr(trade, field_name, value)

            if trade.status == TradeStatus.CLOSED:
                self._open_by_key.pop((trade.strategy, trade.symbol), None)
            elif trade.status == TradeStatus.OPEN:
                self._open_by_key[(trade.strategy, trade.symbol)] = trade.trade_id
            return trade

    def get_trade(self, trade_id: str) -> Optional[Trade]:
        with self._lock:
            return self._trades.get(trade_id)

    def get_all_trades(self) -> List[Trade]:
        with self._lock:
            return list(self._trades.values())

    def get_open_trades(self) -> List[Trade]:
        with self._lock:
            return [self._trades[trade_id] for trade_id in self._open_by_key.values()]

    def get_open_trade(self, strategy: str, symbol: str) -> Optional[Trade]:
        with self._lock:
            trade_id = self._open_by_key.get((strategy, symbol))
            if not trade_id:
                return None
            return self._trades.get(trade_id)

    def has_open_trade_for_symbol(self, symbol: str) -> bool:
        with self._lock:
            return any(trade.symbol == symbol for trade in self.get_open_trades())
