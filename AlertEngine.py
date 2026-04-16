import json
from datetime import datetime
from urllib import parse, request


class TelegramAlertEngine:
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = False):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled and bool(bot_token) and bool(chat_id)

    def _send(self, message: str) -> bool:
        if not self.enabled:
            print(message)
            return False

        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": message,
            }
        ).encode("utf-8")

        req = request.Request(endpoint, data=payload, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with request.urlopen(req, timeout=8) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
                return bool(parsed.get("ok"))
        except Exception as error:
            print(f"Telegram alert error: {error}")
            print(message)
            return False

    def send_entry_alert(self, signal, ltp: float) -> bool:
        ts = datetime.now().strftime("%H:%M:%S")
        message = (
            "ENTRY SIGNAL\n\n"
            f"Strategy: {signal.strategy}\n"
            f"Symbol: {signal.symbol}\n"
            f"Side: {signal.side.value}\n"
            f"Qty: {signal.qty}\n"
            f"Price: {ltp:.2f}\n"
            f"Time: {ts}"
        )
        return self._send(message)

    def send_exit_alert(self, trade, ltp: float, pnl: float) -> bool:
        ts = datetime.now().strftime("%H:%M:%S")
        side = "SELL" if trade.side.value == "BUY" else "BUY"
        message = (
            "EXIT SIGNAL\n\n"
            f"Strategy: {trade.strategy}\n"
            f"Symbol: {trade.symbol}\n"
            f"Side: {side}\n"
            f"Qty: {trade.qty}\n"
            f"Exit Price: {ltp:.2f}\n"
            f"PnL: {pnl:.2f}\n"
            f"Time: {ts}"
        )
        return self._send(message)
