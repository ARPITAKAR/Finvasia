instrument_list= ['EQ', 'INDEX']

option_list= ['NIFTY','ULTRACEMCO']

future_list=['NIFTY']

# runtime mode: "paper" | "alert" | "live"
TRADE_MODE = "alert"

# risk / execution controls
MAX_OPEN_TRADES = 5
ALLOW_MULTIPLE_STRATEGIES_PER_SYMBOL = False
DEFAULT_QTY = 50
PAPER_SLIPPAGE_BPS = 2.0
STOP_LOSS_PCT = 0.005
TARGET_PCT = 0.01
ENGINE_LOOP_SLEEP_SEC = 0.5

# telegram settings
TELEGRAM_ENABLED = False
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
