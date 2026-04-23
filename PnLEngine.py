from typing import Tuple

from models import Side, Trade


def compute_unrealized(trade: Trade, ltp: float) -> float:
    if trade.side == Side.BUY:
        return (ltp - trade.entry_price) * trade.qty
    return (trade.entry_price - ltp) * trade.qty


def compute_realized(trade: Trade) -> float:
    if trade.exit_price is None:
        return 0.0
    if trade.side == Side.BUY:
        return (trade.exit_price - trade.entry_price) * trade.qty
    return (trade.entry_price - trade.exit_price) * trade.qty


def get_stop_target(entry_price: float, side: Side, stop_loss_pct: float, target_pct: float) -> Tuple[float, float]:
    if side == Side.BUY:
        stop_price = entry_price * (1 - stop_loss_pct)
        target_price = entry_price * (1 + target_pct)
    else:
        stop_price = entry_price * (1 + stop_loss_pct)
        target_price = entry_price * (1 - target_pct)
    return stop_price, target_price
