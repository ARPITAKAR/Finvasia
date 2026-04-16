from datetime import datetime

from models import Side, Signal, Trade


class LiveBroker:
    def __init__(self, shoonya_interface):
        self.shoonya_interface = shoonya_interface

    def place_entry(self, signal: Signal, ltp: float) -> dict:
        buy_or_sell = "B" if signal.side == Side.BUY else "S"
        order_id = self.shoonya_interface.TransmitToBroker(
            buy_or_sell=buy_or_sell,
            product_type="M",
            exchange=signal.exchange,
            tradingsymbol=signal.symbol,
            quantity=str(signal.qty),
            discloseqty="0",
            price_type="MKT",
            price=0,
            trigger_price=None,
            retention="DAY",
            remarks=f"{signal.strategy}_entry",
            bookloss_price=None,
            bookprofit_price=0.0,
            trail_price=0.0,
            amo="NO",
        )
        return {
            "order_id": str(order_id),
            "fill_price": float(ltp),
            "fill_time": datetime.now(),
            "status": "FILLED" if int(order_id) != -1 else "REJECTED",
        }

    def place_exit(self, trade: Trade, ltp: float) -> dict:
        buy_or_sell = "S" if trade.side == Side.BUY else "B"
        order_id = self.shoonya_interface.TransmitToBroker(
            buy_or_sell=buy_or_sell,
            product_type="M",
            exchange=trade.meta.get("exchange", "NSE"),
            tradingsymbol=trade.symbol,
            quantity=str(trade.qty),
            discloseqty="0",
            price_type="MKT",
            price=0,
            trigger_price=None,
            retention="DAY",
            remarks=f"{trade.strategy}_exit",
            bookloss_price=None,
            bookprofit_price=0.0,
            trail_price=0.0,
            amo="NO",
        )
        return {
            "order_id": str(order_id),
            "fill_price": float(ltp),
            "fill_time": datetime.now(),
            "status": "FILLED" if int(order_id) != -1 else "REJECTED",
        }
