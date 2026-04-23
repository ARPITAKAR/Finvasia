# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 19:55:13 2026

@author: Arpit
"""

import datetime as dt
import time

import pandas as pd

import settings
from AlertEngine import TelegramAlertEngine
from BrokerAPI.Finvasia.InterfaceFinvasia import InterfaceFinvasia
from ExecutionLive import LiveBroker
from ExecutionPaper import PaperBroker
from Master.MasterFinvasia.MasterSymbolFinvasia import MasterSymbolFinvasia, MasterTypevar
from PnLEngine import compute_realized, compute_unrealized, get_stop_target
from StrategyEngine.TradingStrategy import StrategyEngine
from TradeStore import LiveTradeStore
from Utility.RelativePath import Path
from Utility.SystemCol import SystemCol
from models import ExecutionMode, Side, Signal, Trade, TradeStatus


class TradingEngine:
    def __init__(self):
        print("Welcome to the Trading Engine!")
        self.__shoonyaInterface = InterfaceFinvasia()

        self.df_cash_master = pd.DataFrame()
        self.df_fno_master = pd.DataFrame()
        self.df_trading_strategy = pd.DataFrame()

        self.trade_store = LiveTradeStore()
        self._last_processed_ticks = {}
        self._trade_seq = 0

        mode_value = str(getattr(settings, "TRADE_MODE", "alert")).lower()
        try:
            self.trade_mode = ExecutionMode(mode_value)
        except ValueError:
            self.trade_mode = ExecutionMode.ALERT

        self.execution_engine = None
        if self.trade_mode == ExecutionMode.PAPER:
            self.execution_engine = PaperBroker(getattr(settings, "PAPER_SLIPPAGE_BPS", 2.0))
        elif self.trade_mode == ExecutionMode.LIVE:
            self.execution_engine = LiveBroker(self.__shoonyaInterface)

        self.alert_engine = TelegramAlertEngine(
            bot_token=getattr(settings, "TELEGRAM_BOT_TOKEN", ""),
            chat_id=getattr(settings, "TELEGRAM_CHAT_ID", ""),
            enabled=getattr(settings, "TELEGRAM_ENABLED", False),
        )

        col_name = [
            SystemCol.STRATEGY,
            SystemCol.TRADSYMBOL,
            SystemCol.ENTRYPRICE,
            SystemCol.EXITPRICE,
            SystemCol.PNL,
            SystemCol.LTP,
        ]
        self.df_system = pd.DataFrame(columns=col_name)

        print(f"Engine mode: {self.trade_mode.value}")

    def ConnectBroker(self, broker_name="finvasia"):
        try:
            if broker_name.lower() == "finvasia":
                print("Directing to logging panel Finvasia...")
                self.__shoonyaInterface.login_panel()
        except Exception as error:
            print(f"Error connecting to broker {broker_name}: {error}")

    def StartEngine(self):
        if not self.__shoonyaInterface.isconnected:
            print("Cannot start the Trading Engine. Please connect to the broker first.")
            return

        print("Starting the Trading Engine...")
        self.RequestOrderBook()
        self.RequestExecutedTradeBook()
        self.RequestPositionBook()

        self.__setting_strategy()
        self.MarketFeed()

        self.__shoonyaInterface.CloseConnection()

    def MarketFeed(self):
        try:
            print("Subscribing to market feed...")
            self.__shoonyaInterface.StartStreamingUsingWebSocket()
            client_tokens = ["NSE|3563", "NSE|25"]
            self.__shoonyaInterface.SubscribeTokenToBroker(tokenlist=client_tokens)
            self.SubscribeToLiveFeed()

            while True:
                self.process_new_ticks()
                self.monitor_open_trades()
                time.sleep(getattr(settings, "ENGINE_LOOP_SLEEP_SEC", 0.5))

        except KeyboardInterrupt:
            print("Market feed streaming stopped by user.")
            self.__shoonyaInterface.CloseConnection()
        except Exception as error:
            print(f"Error in MarketFeed: {error}")

    def process_new_ticks(self):
        df = self.__shoonyaInterface.df_feed
        if df.empty:
            return

        for _, row in df.iterrows():
            token = str(row.get("Token", ""))
            if not token:
                continue

            last_updated = row.get("LastUpdated")
            if pd.isnull(last_updated):
                continue

            previous = self._last_processed_ticks.get(token)
            if previous is not None and last_updated <= previous:
                continue

            self._last_processed_ticks[token] = last_updated
            self.on_tick(row)

    def on_tick(self, row):
        signals = self.generate_signals_from_tick(row)
        if not signals:
            return

        ltp = float(row.get("LTP", 0.0))
        for signal in signals:
            if self.can_take_entry(signal, ltp):
                self._open_trade(signal, ltp)

    def generate_signals_from_tick(self, row):
        exclude_symbols = {"INDIA VIX", "NIFTY INDEX", "NIFTY BANK", "FINNIFTY", "MIDCPNIFTY"}
        stale_threshold_seconds = 5

        symbol = str(row.get("TradingSymbol", "")).strip()
        if not symbol or symbol in exclude_symbols or symbol == "NA":
            return []

        last_updated = row.get("LastUpdated")
        if pd.isnull(last_updated):
            return []
        if (dt.datetime.now() - last_updated).seconds > stale_threshold_seconds:
            return []

        ltp = float(row.get("LTP", 0.0))
        if ltp <= 0:
            return []

        open_price = float(row.get("Open", 0.0))
        high_price = float(row.get("High", 0.0))
        low_price = float(row.get("Low", 0.0))
        close_price = float(row.get("Close", 0.0))

        candle_range = high_price - low_price
        if candle_range <= 0:
            return []

        body_length = abs(open_price - close_price)
        body_condition = body_length <= (candle_range * 0.10)

        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price

        wick_condition = upper_wick >= 2 * lower_wick or lower_wick >= 2 * upper_wick
        if not body_condition or not wick_condition:
            return []

        side = Side.BUY if lower_wick > upper_wick else Side.SELL
        token = str(row.get("Token", ""))

        signal = Signal(
            strategy="WICK_DOMINANT_V1",
            symbol=symbol,
            side=side,
            qty=int(getattr(settings, "DEFAULT_QTY", 10)),
            exchange=self._infer_exchange(symbol),
            token=token,
            meta={"token": token},
        )
        print(
            f"Signal -> Strategy:{signal.strategy} Symbol:{signal.symbol} "
            f"Side:{signal.side.value} LTP:{ltp:.2f}"
        )
        return [signal]

    def can_take_entry(self, signal: Signal, ltp: float):
        if ltp <= 0 or signal.qty <= 0:
            return False

        open_trades = self.trade_store.get_open_trades()
        if len(open_trades) >= int(getattr(settings, "MAX_OPEN_TRADES", 5)):
            return False

        allow_multi = bool(getattr(settings, "ALLOW_MULTIPLE_STRATEGIES_PER_SYMBOL", False))
        if not allow_multi and self.trade_store.has_open_trade_for_symbol(signal.symbol):
            return False

        if self.trade_store.get_open_trade(signal.strategy, signal.symbol):
            return False

        return True

    def _next_trade_id(self):
        self._trade_seq += 1
        return f"TRD-{self._trade_seq:06d}"

    def _open_trade(self, signal: Signal, ltp: float):
        if self.trade_mode == ExecutionMode.ALERT:
            self.alert_engine.send_entry_alert(signal, ltp)
            fill = {
                "order_id": f"ALERT-ENTRY-{self._trade_seq + 1}",
                "fill_price": float(ltp),
                "fill_time": dt.datetime.now(),
                "status": "FILLED",
            }
        else:
            fill = self.execution_engine.place_entry(signal, ltp)

        if fill.get("status") != "FILLED":
            print(f"Entry rejected for {signal.symbol}")
            return None

        fill_price = float(fill["fill_price"])
        stop_price, target_price = get_stop_target(
            entry_price=fill_price,
            side=signal.side,
            stop_loss_pct=float(getattr(settings, "STOP_LOSS_PCT", 0.005)),
            target_pct=float(getattr(settings, "TARGET_PCT", 0.01)),
        )

        trade = Trade(
            trade_id=self._next_trade_id(),
            strategy=signal.strategy,
            symbol=signal.symbol,
            side=signal.side,
            qty=signal.qty,
            entry_price=fill_price,
            entry_time=fill["fill_time"],
            meta={
                "exchange": signal.exchange,
                "token": signal.token,
                "entry_order_id": fill.get("order_id"),
                "stop_price": stop_price,
                "target_price": target_price,
                "mode": self.trade_mode.value,
            },
        )
        self.trade_store.add_trade(trade)

        print(
            f"Trade OPEN -> ID:{trade.trade_id} Symbol:{trade.symbol} "
            f"Entry:{trade.entry_price:.2f} Stop:{stop_price:.2f} Target:{target_price:.2f}"
        )
        return trade

    def monitor_open_trades(self):
        open_trades = list(self.trade_store.get_open_trades())
        for trade in open_trades:
            ltp = self._get_ltp_for_symbol(trade.symbol)
            if ltp is None:
                continue

            unrealized = compute_unrealized(trade, ltp)
            self.trade_store.update_trade(trade.trade_id, unrealized_pnl=unrealized)

            if self._should_exit(trade, ltp):
                self._close_trade(trade, ltp)

        self._refresh_system_dataframe()

    def _should_exit(self, trade: Trade, ltp: float):
        stop_price = float(trade.meta.get("stop_price", 0.0))
        target_price = float(trade.meta.get("target_price", 0.0))

        if trade.side == Side.BUY:
            return ltp <= stop_price or ltp >= target_price
        return ltp >= stop_price or ltp <= target_price

    def _close_trade(self, trade: Trade, ltp: float):
        expected_pnl = compute_unrealized(trade, ltp)

        if self.trade_mode == ExecutionMode.ALERT:
            self.alert_engine.send_exit_alert(trade, ltp, expected_pnl)
            fill = {
                "order_id": f"ALERT-EXIT-{trade.trade_id}",
                "fill_price": float(ltp),
                "fill_time": dt.datetime.now(),
                "status": "FILLED",
            }
        else:
            fill = self.execution_engine.place_exit(trade, ltp)

        if fill.get("status") != "FILLED":
            print(f"Exit rejected for {trade.trade_id}")
            return

        exit_price = float(fill["fill_price"])
        realized = compute_realized(
            Trade(
                trade_id=trade.trade_id,
                strategy=trade.strategy,
                symbol=trade.symbol,
                side=trade.side,
                qty=trade.qty,
                entry_price=trade.entry_price,
                entry_time=trade.entry_time,
                status=TradeStatus.CLOSED,
                exit_price=exit_price,
                exit_time=fill["fill_time"],
                meta=trade.meta,
            )
        )

        self.trade_store.update_trade(
            trade.trade_id,
            exit_price=exit_price,
            exit_time=fill["fill_time"],
            realized_pnl=realized,
            unrealized_pnl=0.0,
            status=TradeStatus.CLOSED,
        )

        print(
            f"Trade CLOSED -> ID:{trade.trade_id} Symbol:{trade.symbol} "
            f"Exit:{exit_price:.2f} PnL:{realized:.2f}"
        )

    def _get_ltp_for_symbol(self, symbol: str):
        df = self.__shoonyaInterface.df_feed
        if df.empty:
            return None

        matched = df[df["TradingSymbol"] == symbol]
        if matched.empty:
            return None

        ltp = float(matched.iloc[-1].get("LTP", 0.0))
        if ltp <= 0:
            return None
        return ltp

    def _infer_exchange(self, trading_symbol: str):
        if not self.df_fno_master.empty and trading_symbol in set(self.df_fno_master["TradingSymbol"]):
            return "NFO"
        return "NSE"

    def _refresh_system_dataframe(self):
        rows = []
        for trade in self.trade_store.get_open_trades():
            ltp = self._get_ltp_for_symbol(trade.symbol)
            rows.append(
                {
                    SystemCol.STRATEGY: trade.strategy,
                    SystemCol.TRADSYMBOL: trade.symbol,
                    SystemCol.ENTRYPRICE: trade.entry_price,
                    SystemCol.EXITPRICE: trade.exit_price,
                    SystemCol.PNL: trade.unrealized_pnl,
                    SystemCol.LTP: ltp,
                }
            )
        self.df_system = pd.DataFrame(rows, columns=self.df_system.columns)

    def RequestOrderBook(self):
        try:
            print("Requesting order book...")
            self.__shoonyaInterface.GetCompleteOrderBook()
        except Exception as error:
            print(f"Error requesting order book: {error}")

    def RequestExecutedTradeBook(self):
        try:
            print("Requesting executed trade book...")
            get_trade_book = self.__shoonyaInterface.GetExecutedTradeBookFromTradingVenue()
            if get_trade_book:
                for trade in get_trade_book:
                    print(f"trade details: {trade}")
        except Exception as error:
            print(f"Error requesting executed trade book: {error}")

    def RequestPositionBook(self):
        try:
            print("Requesting position book...")
            self.__shoonyaInterface.GetNetPositionForToken()
        except Exception as error:
            print(f"Error requesting position book: {error}")

    def MasterSymbolDownload(self):
        try:
            print("Processing master symbol file...")
            print("Please wait while the master symbol file is being downloaded...")

            full_path = Path.relative_path()
            print(f"Full path: {full_path}")
            master = MasterSymbolFinvasia(full_path)
            master.PrepareUrl()
            master.DownloadMaster(MasterTypevar.With_Cash_Fno)
            master.ReadMasterTextFile(MasterTypevar.With_Cash_Fno)

            self.df_cash_master = master.GetCashMasterDataFrame()
            self.df_fno_master = master.GetFnoMasterDataFrame()

            print("Cash master size BEFORE filter:", len(self.df_cash_master))
            print("FNO master size BEFORE filter:", len(self.df_fno_master))

            self.apply_instruments_filter()
            print("Cash master size AFTER filter:", len(self.df_cash_master))

            self.apply_instrument_filterFNO()
            print("FNO master size AFTER filter:", len(self.df_fno_master))
            self._build_symbol_map()
        except Exception as error:
            print(f"Error downloading master symbol file: {error}")

    def apply_instruments_filter(self):
        try:
            print("Applying instrument filter...")
            print("Instrument list from settings:", settings.instrument_list)
            print("Before filtering:", len(self.df_cash_master))
            if self.df_cash_master.empty:
                print("Master symbol dataframes are empty. Please download master symbols first.")
                return

            self.df_cash_master = self.df_cash_master[self.df_cash_master["Instrument"].isin(settings.instrument_list)]
            print("After filtering:", len(self.df_cash_master))
        except Exception as error:
            print(f"Error applying instruments filter: {error}")

    def SubscribeToLiveFeed(self):
        try:
            if not isinstance(self.__shoonyaInterface, InterfaceFinvasia):
                raise AttributeError(
                    "ShoonyaInterface is not an instance of InterfaceFinvasia. Please check the connection to the broker."
                )

            if len(self.df_cash_master) == 0:
                raise ValueError("Master symbol dataframes are empty. Please download master symbols first.")

            token_list = list(self.df_cash_master["Token"][:5])
            formatted_token_list = [f"NSE|{token}" for token in token_list]
            print(f"Subscribing to live feed for {len(formatted_token_list)} symbols...")
            self.__shoonyaInterface.SubscribeTokenToBroker(tokenlist=formatted_token_list)

        except Exception as error:
            print(f"Error subscribing to live feed: {error}")

    def SubscribeToLiveFeedFno(self):
        try:
            if not isinstance(self.__shoonyaInterface, InterfaceFinvasia):
                raise AttributeError(
                    "ShoonyaInterface is not an instance of InterfaceFinvasia. Please check the connection to the broker."
                )

            if len(self.df_fno_master) == 0:
                raise ValueError("Master symbol dataframes are empty. Please download master symbols first.")

            token_list = list(self.df_fno_master["Token"][:4])
            formatted_token_list_fno = [f"NFO|{token}" for token in token_list]
            print(f"Subscribing to live feed for {len(formatted_token_list_fno)} symbols...")
            self.__shoonyaInterface.SubscribeTokenToBroker(tokenlist=formatted_token_list_fno)

        except Exception as error:
            print(f"Error subscribing to live feed: {error}")

    def apply_instrument_filterFNO(self):
        try:
            print("Applying instrument filter...")
            print("Instrument list from settings:", settings.future_list)
            print("Before filtering:", len(self.df_fno_master))

            if self.df_fno_master.empty:
                print("Master symbol dataframes are empty. Please download NFO master symbols first.")
                return

            self.df_fno_master = self.df_fno_master[self.df_fno_master["Symbol"].isin(settings.future_list)]
            self.df_fno_master["Expiry"] = pd.to_datetime(self.df_fno_master["Expiry"], format="%d-%b-%Y")

            current_year = dt.datetime.now().year
            self.df_fno_master = self.df_fno_master[self.df_fno_master["Expiry"].dt.year == current_year]
            print("After filtering:", len(self.df_fno_master))

        except Exception as error:
            print(f"Error applying instruments filter: {error}")

    def __setting_strategy(self):
        self.df_trading_strategy = pd.DataFrame()
        self.loading_trading_strategy()

    def loading_trading_strategy(self):
        print("Loading trading strategy function in trading engine")
        try:
            strategy_engine = StrategyEngine(self.df_fno_master,self.df_cash_master)
            strategy_engine._load_fno_strategy("NIFTY", 25000)
            strategy_engine._load_cash_strategy("RelianceEQ",2200)
            self.df_trading_strategy = strategy_engine.get_trading_strategy()

            if self.df_trading_strategy is None or self.df_trading_strategy.empty:
                print("Trading strategy is empty")
        except Exception as error:
            print(f"Error generated while loading strategy: {error}")

    def _build_symbol_map(self):
        symbol_map = {}

        if not self.df_cash_master.empty:
            cash_map = dict(
                zip(
                    self.df_cash_master["Token"].astype(str),
                    self.df_cash_master["TradingSymbol"],
                )
            )
            symbol_map.update(cash_map)

        if not self.df_fno_master.empty:
            fno_map = dict(
                zip(
                    self.df_fno_master["Token"].astype(str),
                    self.df_fno_master["TradingSymbol"],
                )
            )
            symbol_map.update(fno_map)

        print(f"Symbol map built: {len(symbol_map)} tokens total.")
        self.__shoonyaInterface.LoadSymbolMap(symbol_map)

    def get_trading_symbol(self, symbol, expiry=None, option_type=None, strike=None, exchange=None):
        try:
            if exchange == "NSE":
                df = self.df_cash_master[self.df_cash_master["Symbol"] == symbol]
                if not df.empty:
                    return df.iloc[0]["TradingSymbol"]

            elif exchange == "NFO":
                df = self.df_fno_master[(self.df_fno_master["Symbol"] == symbol)]

                if expiry:
                    df = df[df["Expiry"].dt.strftime("%d-%b-%Y") == expiry]

                if option_type:
                    df = df[df["OptionType"] == option_type]

                if strike:
                    df = df[df["StrikePrice"] == int(strike)]

                if not df.empty:
                    return df.iloc[0]["TradingSymbol"]

            print("No matching trading symbol found")
            return None

        except Exception as error:
            print(f"Error in get_trading_symbol: {error}")
            return None
