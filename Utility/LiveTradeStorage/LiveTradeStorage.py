# File: LiveTradeStore.py

# Function: __init__
class LiveTradeStore:
    def __init__(self):
        print("[INFO] initializing live trades Storage.")
        self.trades = {}

# Function: add_trade
    def add_trade(self, trade_data):
        trade_id = trade_data["trade_id"]
        if trade_id in self.trades:
            print(f"[WARN] Trade {trade_id} already exists")
            return
        self.trades[trade_id] = trade_data

# Function: update_trade
    def update_trade(self, trade_id, updates: dict):
        if trade_id not in self.trades:
            print(f"[ERROR] Trade {trade_id} not found")
            return
        self.trades[trade_id].update(updates)

# Function: get_all_trades
    def get_all_trades(self):
        return list(self.trades.values())

# Function: get_trade
    def get_trade(self, trade_id):
        
        return self.trades.get(trade_id, None)