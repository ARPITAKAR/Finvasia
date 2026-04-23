from datetime import datetime

from models import Side, Signal, Trade


class PaperBroker:
    def __init__(self, slippage_bps: float = 2.0):
        self.slippage_bps = slippage_bps

    def _apply_slippage(self, ltp: float, side: Side) -> float:
        slippage = self.slippage_bps / 10000.0
        if side == Side.BUY:
            return ltp * (1 + slippage)
        return ltp * (1 - slippage)

    def place_entry(self, signal: Signal, ltp: float) -> dict:
        fill_price = self._apply_slippage(ltp, signal.side)
        return {
            "order_id": f"PAPER-ENTRY-{int(datetime.now().timestamp() * 1000)}",
            "fill_price": round(fill_price, 2),
            "fill_time": datetime.now(),
            "status": "FILLED",
        }

    def place_exit(self, trade: Trade, ltp: float) -> dict:
        exit_side = Side.SELL if trade.side == Side.BUY else Side.BUY
        fill_price = self._apply_slippage(ltp, exit_side)
        return {
            "order_id": f"PAPER-EXIT-{int(datetime.now().timestamp() * 1000)}",
            "fill_price": round(fill_price, 2),
            "fill_time": datetime.now(),
            "status": "FILLED",
        }
