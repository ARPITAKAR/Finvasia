# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 19:55:13 2026

@author: Arpit
"""

import token
import time
import pandas as pd
from BrokerAPI.Finvasia.api_helper import ShoonyaApiPy
from Credentials.credbrokers import CredentialFinvasia
from BrokerAPI.Finvasia.InterfaceFinvasia import InterfaceFinvasia
from Master.MasterFinvasia.MasterSymbolFinvasia import MasterSymbolFinvasia, MasterTypevar
from Utility.RelativePath import Path
import settings
import datetime as dt


class TradingEngine:
    def __init__(self):
        print("Welcome to the Trading Engine!")
        self.__shoonyaInterface = InterfaceFinvasia()

        self.df_cash_master = pd.DataFrame()
        self.df_fno_master = pd.DataFrame()

    def ConnectBroker(self, broker_name="finvasia"):
        try:
            if broker_name.lower() == "finvasia":
                print("Directing to logging panel Finvasia...")
                self.__shoonyaInterface.login_panel()
        except Exception as e:
            print(f"Error connecting to broker {broker_name}: {e}")
        
    def StartEngine(self):
        if self.__shoonyaInterface.isconnected:
            print("Starting the Trading Engine...")
            # if self.__shoonyaInterface.RequestToBroker():
            #     print("Trading Engine started successfully.")
            #     self.TakeNewEntry()
            # else:
            #     print("Failed to start the Trading Engine. Please check the connection and try again.")
        else:
            print("Cannot start the Trading Engine. Please connect to the broker first.")
            
        self.RequestOrderBook()  # Request order book before starting market feed
        self.RequestExecutedTradeBook()  # Request executed trade book before starting market feed    
        self.RequestPositionBook()  # Request position book before starting market feed
        self.MarketFeed()
        
        self.__shoonyaInterface.CloseConnection()
        
    def TakeNewEntry(self):
        try:
            print("Taking new entry...")
            buy_or_sell = input("Enter B -> BUY, S -> SELL: ").strip().upper()
            product_type = input("Enter product type (e.g., 'C' for Carry,M ,H): ").strip().upper()
            exchange=input("Enter exchange (e.g. Exchange NSE / NFO / BSE / CDS): ").strip().upper()
            tradingsymbol = input("Enter trading symbol (e.g., 'CANBK-EQ'): ").strip().upper()
            quantity = str(input("Enter quantity: "))
            discloseqty = str(input("Enter disclose quantity (0 if none): "))
            price_type = input("Enter price type (e.g., 'LMT'): ")
            price= int(input("Enter price: "))
            trigger_price= int(input("Enter trigger price: "))
            retention = input("Enter retention (e.g., DAY / IOC / EOS): ")
            remarks = input("Enter remarks for the order: ")
            bookloss_price=None
            bookprofit_price=0.0
            trail_price=0.0
            amo=input("Is this an AMO order? (YES/NO): ").strip().upper()
            
            rec_ordeid=self.__shoonyaInterface.TransmitToBroker(buy_or_sell=buy_or_sell, product_type=product_type, exchange=exchange, tradingsymbol=tradingsymbol, quantity=quantity, discloseqty=discloseqty, price_type=price_type,price=price, trigger_price=trigger_price, retention=retention,remarks=remarks,bookloss_price=bookloss_price, bookprofit_price=bookprofit_price,trail_price=trail_price,amo=amo)
                                                            
            if rec_ordeid != -1:
                print(f"Order placed successfully. Received Order ID: {rec_ordeid}")
            else:
                print("Not able to take new entry order, rec_orderid -1.")
            
        except Exception as e:
            print(f"Error taking new entry: {e}")
            
    # Get Market feed through websocket connection and implement your strategy logic here
    def MarketFeed(self):
        try:
            print("Subscribing to market feed...")
            self.__shoonyaInterface.StartStreamingUsingWebSocket()
            client_tokens= ['NSE|3563','NSE|25']  # Example tokens, replace with actual tokens you want to subscribe to
            self.__shoonyaInterface.SubscribeTokenToBroker(tokenlist=client_tokens)  # Subscribe to tokens dynamically
            self.SubscribeToLiveFeed()  # Subscribe to live feed for the symbols present in the master symbol dataframes
            self.SubscribeToLiveFeedFno()
            try:
                while True:
                    time.sleep(0.5)  # Keep the main thread alive to continue receiving market feed through WebSocket
            except KeyboardInterrupt:
                print("Market feed streaming stopped by user.")
                self.__shoonyaInterface.CloseConnection()  # Close the WebSocket connection when stopping the market feed
        
        except Exception as e:
            print(f"Error in MarketFeed: {e}")
            
    # Function 6: Request Order Book from Trading venue
    def RequestOrderBook(self):
        try:
            print("Requesting order book...")
            self.__shoonyaInterface.GetCompleteOrderBook()
        except Exception as e:
            print(f"Error requesting order book: {e}")
            
    # Function 7: Request Executed Trade Book from Trading venue
    def RequestExecutedTradeBook(self):
        try:
            print("Requesting executed trade book...")
            getTradeBook = self.__shoonyaInterface.GetExecutedTradeBookFromTradingVenue()
            for trade in getTradeBook:
                # Process each trade as needed (e.g., print details, update strategy, etc.)
                print(f"trade details: {trade}")
        except Exception as e:
            print(f"Error requesting executed trade book: {e}")
               
                
    # Function 8: Request Position Book from Trading venue
    def RequestPositionBook(self):
        try:
            print("Requesting position book...")
            self.__shoonyaInterface.GetNetPositionForToken()
        except Exception as e:
            print(f"Error requesting position book: {e}")
            
    # Function 9: Downloading Master File
    def MasterSymbolDownload(self):
        try:
            print("Processing master symbol file...")
            print("Please wait while the master symbol file is being downloaded...")
            
            full_path= Path.relative_path()
            print(f"Full path: {full_path}")
            __master= MasterSymbolFinvasia(full_path)
            __master.PrepareUrl()
            __master.DownloadMaster(MasterTypevar.With_Cash_Fno)
            __master.ReadMasterTextFile(MasterTypevar.With_Cash_Fno)

            self.df_cash_master= __master.GetCashMasterDataFrame()
            self.df_fno_master= __master.GetFnoMasterDataFrame()
            
            print("Cash master size BEFORE filter:", len(self.df_cash_master))
            print("FNO master size BEFORE filter:", len(self.df_fno_master))
            

            self.apply_instruments_filter()  # Apply filter on the master symbol dataframes based on the instrument list defined in settings.py
            print("Cash master size AFTER filter:", len(self.df_cash_master))

            self.apply_instrument_filterFNO()
            print("FNO master size AFTER filter:", len(self.df_fno_master))
            
        except Exception as e:
            print(f"Error downloading master symbol file: {e}")

    # Function 10: Filter on the basis of Sector

    
    def apply_instruments_filter(self):
        """Filter the master symbol dataframes based on the instrument list defined in settings.py."""
        try:
            print("Applying instrument filter...")
            print("Instrument list from settings:", settings.instrument_list)
            print("Before filtering:", len(self.df_cash_master))
            if self.df_cash_master.empty:
                print("Master symbol dataframes are empty. Please download master symbols first.")
                return

            self.df_cash_master = self.df_cash_master[
                self.df_cash_master['Instrument'].isin(settings.instrument_list)
            ]
            print("After filtering:", len(self.df_cash_master))
        except Exception as e:
            print(f"Error applying instruments filter: {e}")

# Function 11: Subscribe to live feed from cluster dataframe

    def SubscribeToLiveFeed(self):
        """ Subscribe to live feed for the symbols present in the master symbol dataframes."""

        try:
            if not isinstance(self.__shoonyaInterface, InterfaceFinvasia):
                raise AttributeError("ShoonyaInterface is not an instance of InterfaceFinvasia. Please check the connection to the broker.")
            
            if len(self.df_cash_master) == 0:
                print("No symbols to subscribe to. Please check the master symbol dataframes.")
                raise ValueError("Master symbol dataframes are empty. Please download master symbols first.")
            
            stocks_list= list(self.df_cash_master['Symbol'])
            token_list= list(self.df_cash_master['Token'])
            formatted_token_list= [f"NSE|{token}" for token in token_list]  # Format tokens as required by the broker API
            print(f"Subscribing to live feed for {len(formatted_token_list)} symbols...")

            formatted_token_list = formatted_token_list[:50]
            '''Subscribe to tokens dynamically based on the master symbol dataframe'''
            self.__shoonyaInterface.SubscribeTokenToBroker(tokenlist=formatted_token_list) 
            

        except Exception as e:
            print(f"Error subscribing to live feed: {e}")

# Exchange,Token,LotSize,Symbol,TradingSymbol,Expiry,Instrument,OptionType,StrikePrice,TickSize

    # Function 12: Filter on the basis of cluster-FNO
        

    def apply_instrument_filterFNO(self):

        try:
            print("Applying instrument filter...")
            print("Instrument list from settings:", settings.future_optionlist)
            print("Before filtering:", len(self.df_fno_master))

            if self.df_fno_master.empty:
                print("Master symbol dataframes are empty. Please download NFO master symbols first.")
                return

            # Filter symbols
            self.df_fno_master = self.df_fno_master[
                self.df_fno_master['Symbol'].isin(settings.future_optionlist)
            ]

            # Convert expiry to datetime
            self.df_fno_master['Expiry'] = pd.to_datetime(self.df_fno_master['Expiry'], format='%d-%b-%Y')

            # Get current year
            current_year = dt.datetime.now().year

            # Filter only current year expiry
            self.df_fno_master = self.df_fno_master[
                self.df_fno_master['Expiry'].dt.year == current_year
            ]
            

            print("After filtering:", len(self.df_fno_master))

        except Exception as e:
            print(f"Error applying instruments filter: {e}")

        
# Function 13: Subscribe to live feed from cluster dataframe

    def SubscribeToLiveFeedFno(self):
        """ Subscribe to live feed for the Options and Futures symbols present in the master dataframes."""

        try:
            if not isinstance(self.__shoonyaInterface, InterfaceFinvasia):
                raise AttributeError("ShoonyaInterface is not an instance of InterfaceFinvasia. Please check the connection to the broker.")
            
            if len(self.df_fno_master) == 0:
                print("No symbols to subscribe to. Please check the master symbol dataframes.")
                raise ValueError("Master symbol dataframes are empty. Please download master symbols first.")
            
            stocks_list= list(self.df_fno_master['Symbol'])
            token_list= list(self.df_fno_master['Token'])
            formatted_token_list_fno= [f"NFO|{token}" for token in token_list]  # Format tokens as required by the broker API
            print(f"Subscribing to live feed for {len(formatted_token_list_fno)} symbols...")

            '''Subscribe to tokens dynamically based on the master symbol dataframe'''
            self.__shoonyaInterface.SubscribeTokenToBroker(tokenlist=formatted_token_list_fno) 
            
        except Exception as e:
            print(f"Error subscribing to live feed: {e}")
